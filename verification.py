"""Offline quality and spend-state helpers. Single-writer, no live API calls.

Persist a reservation before sending externally. An uncertain submission blocks
all further reservations, including after a restart. Reconciliation is an
operator assertion, not an authenticated billing receipt. No automatic replay.
"""
import copy
import json
import math
import os
import re
import tempfile
import unicodedata
from pathlib import Path

from suno_optimizer import require, integer

def lyric_normalize(text):
    require(isinstance(text,str) and len(text)<=5000,"invalid transcript")
    text=unicodedata.normalize("NFKC",text)
    # Strip only known standalone section labels. Preserve kanji/kana,
    # pronunciation differences and all other content except punctuation/space.
    text="\n".join(line for line in text.splitlines()
        if not re.fullmatch(r"\s*\[(?:verse|chorus|bridge|intro|outro|pre-chorus|hook)(?:\s+\d+)?\]\s*",line,re.I))
    return "".join(c for c in text if not c.isspace() and not unicodedata.category(c).startswith("P"))

def lyric_cer(reference,transcript,human_reviewed=False):
    ref=lyric_normalize(reference)
    hyp=lyric_normalize(transcript) if transcript is not None else ""
    if not ref or transcript is None:
        return {"status":"UNKNOWN","cer":None,"source":"UNVERIFIED"}
    # Levenshtein distance; insertion errors may make CER > 1.
    prev=list(range(len(hyp)+1))
    for i,a in enumerate(ref,1):
        cur=[i]
        for j,b in enumerate(hyp,1):
            cur.append(min(cur[-1]+1,prev[j]+1,prev[j-1]+(a!=b)))
        prev=cur
    return {"status":("PASS" if prev[-1]==0 else "FAIL") if human_reviewed is True else "UNKNOWN",
            "cer":prev[-1]/len(ref),"edit_distance":prev[-1],
            "reference_characters":len(ref),"source":"HUMAN" if human_reviewed is True else "UNVERIFIED",
            "normalization":"nfkc-known-section-labels-punctuation-space-v1",
            "pronunciation_verified":False}

def new_run(budget,max_calls,max_candidates,max_elapsed_s):
    for k,v in (("budget",budget),("max_calls",max_calls),("max_candidates",max_candidates),("max_elapsed_s",max_elapsed_s)):
        integer(v,k,1,1_000_000)
    return {"version":1,"budget":budget,"max_calls":max_calls,
            "max_candidates":max_candidates,"max_elapsed_s":max_elapsed_s,
            "attempts":[]}

def totals(run):
    rows=run["attempts"]
    return {"spent":sum(r["actual_cost"] for r in rows if r["state"]=="RECONCILED"),
            "reserved":sum(r["upper_cost"] for r in rows if r["state"]=="SUBMISSION_UNKNOWN"),
            "calls":len(rows),"candidates":sum(len(r["candidate_ids"]) for r in rows if r["state"]=="RECONCILED"),
            "pending":sum(r["state"]=="SUBMISSION_UNKNOWN" for r in rows)}

def reserve(run,attempt_id,fingerprint,approved_fingerprint,upper_cost,expected_count,elapsed_s,available_credits):
    """Return a new checkpoint, not permission to call a remote API."""
    t=totals(run)
    require(t["pending"]==0,"unresolved submission")
    require(isinstance(attempt_id,str) and 0<len(attempt_id)<=128 and all(r["attempt_id"]!=attempt_id for r in run["attempts"]),"duplicate/invalid attempt")
    require(isinstance(fingerprint,str) and bool(re.fullmatch("[0-9a-f]{64}",fingerprint)) and fingerprint==approved_fingerprint,"exact approval required")
    integer(upper_cost,"upper_cost",1,1_000_000)
    integer(expected_count,"expected_count",1,100)
    integer(elapsed_s,"elapsed_s",0,1_000_000)
    integer(available_credits,"available_credits",0,1_000_000)
    require(elapsed_s<run["max_elapsed_s"] and t["calls"]<run["max_calls"],"time/call limit")
    require(t["candidates"]+expected_count<=run["max_candidates"],"candidate limit")
    require(t["spent"]+upper_cost<=run["budget"] and upper_cost<=available_credits,"insufficient budget")
    out=copy.deepcopy(run)
    out["attempts"].append({"attempt_id":attempt_id,"fingerprint":fingerprint,"upper_cost":upper_cost,
        "expected_count":expected_count,"state":"SUBMISSION_UNKNOWN","candidate_ids":[],"actual_cost":None})
    return out

def reconcile(run,attempt_id,candidate_ids,actual_cost,confirmed=False):
    """Only mark resolved if identity/count and observed cost are reconciled."""
    require(confirmed is True,"operator evidence confirmation required")
    require(totals(run)["pending"]==1,"no single pending submission")
    row=next(r for r in run["attempts"] if r["state"]=="SUBMISSION_UNKNOWN")
    require(row["attempt_id"]==attempt_id,"wrong attempt")
    require(isinstance(candidate_ids,list) and len(candidate_ids)==row["expected_count"] and
            all(isinstance(x,str) and x and len(x)<=256 for x in candidate_ids) and
            len(set(candidate_ids))==len(candidate_ids),"unexpected candidate set")
    require(not set(candidate_ids).intersection(x for r in run["attempts"] for x in r["candidate_ids"]),"candidate reused")
    integer(actual_cost,"actual_cost",1,row["upper_cost"])
    out=copy.deepcopy(run)
    r=next(x for x in out["attempts"] if x["attempt_id"]==attempt_id)
    r.update(state="RECONCILED",candidate_ids=candidate_ids.copy(),actual_cost=actual_cost)
    return out

def save_checkpoint(path,run):
    """Atomic replacement within an existing private local directory."""
    p=Path(path)
    require(p.parent.is_dir(),"private checkpoint directory must exist")
    fd,tmp=tempfile.mkstemp(prefix=".sgo-",dir=p.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as f:
            json.dump(run,f,ensure_ascii=False,allow_nan=False)
            f.flush(); os.fsync(f.fileno())
        os.replace(tmp,p)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def load_checkpoint(path):
    """Validate trusted local checkpoint structure by reconstructing events.

    Not tamper-proof: never use externally supplied checkpoints as authority.
    """
    p=Path(path)
    require(p.stat().st_size<=2_000_000,"checkpoint too large")
    d=json.loads(p.read_text(encoding="utf-8"))
    require(d.get("version")==1 and isinstance(d.get("attempts"),list),"bad checkpoint")
    out=new_run(*(d[k] for k in ("budget","max_calls","max_candidates","max_elapsed_s")))
    for r in d["attempts"]:
        out=reserve(out,r["attempt_id"],r["fingerprint"],r["fingerprint"],r["upper_cost"],r["expected_count"],0,1_000_000)
        if r["state"]=="RECONCILED":
            out=reconcile(out,r["attempt_id"],r["candidate_ids"],r["actual_cost"],True)
        else:
            require(r["state"]=="SUBMISSION_UNKNOWN","unknown checkpoint state")
    require(out==d,"checkpoint mismatch")
    return out
