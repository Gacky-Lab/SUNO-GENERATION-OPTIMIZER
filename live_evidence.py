"""Provider evidence and bounded feedback research helpers. No network or writes to Suno."""
import argparse
import json
import math
from suno_optimizer import require, unwrap, read_json, digest, canonical, integer

def number(v, low, high):
    return type(v) in (int, float) and math.isfinite(v) and low <= v <= high

def wait_summary(result, expected):
    require(isinstance(expected,list) and expected and all(isinstance(x,str) and x for x in expected)
            and len(set(expected))==len(expected), "invalid expected IDs")
    data = unwrap(result)
    clips = data.get("clips", [data])
    require(isinstance(clips,list) and all(isinstance(c,dict) for c in clips), "invalid clip list")
    ids = [c.get("id") for c in clips]
    require(ids==expected, "missing, duplicate or reordered candidates")
    states = []
    for c in clips:
        status = c.get("status")
        if c.get("error"):
            status = "error"
        require(status in ("queued","pending","processing","streaming","complete","error"),
                "unrecognized clip status")
        states.append(status)
    return {"states":states,"all_terminal":all(s in ("complete","error") for s in states),
            "complete_count":states.count("complete"),"error_count":states.count("error")}

def provider_evidence(retrieve, analysis, alignment):
    """Redacted derived metrics, never full lyrics, IDs, URLs or song metadata."""
    r,a,l = map(unwrap,(retrieve,analysis,alignment))
    require(isinstance(r.get("id"),str) and r["id"]==a.get("audio_id")==l.get("audio_id"),
            "mismatched evidence IDs")
    require(r.get("status")=="complete","audio not complete")
    require(a.get("status") in ("processing","complete","unavailable"),"unknown analysis status")
    require(l.get("status") in ("processing","complete","unavailable"),"unknown alignment status")
    m=r.get("metadata")
    require(isinstance(m,dict),"metadata absent")
    duration=m.get("duration")
    bpm=a.get("bpm")
    audio_duration=a.get("duration_s")
    def valid(v,lo,hi):
        return v if number(v,lo,hi) else None
    words=l.get("words")
    require(isinstance(words,list),"words absent")
    valid_words = 0
    for w in words:
        require(isinstance(w,dict),"invalid word entry")
        start,end=w.get("start_s"),w.get("end_s")
        if w.get("success") is True and number(start,0,3600) and number(end,start,3600):
            valid_words += 1
    return {"source":"SUNO_PROVIDER_NOT_INDEPENDENT","retrieve_status":"complete",
            "analysis_status":a["status"],"alignment_status":l["status"],
            "provider_duration_seconds":valid(duration,0.001,3600),
            "analysis_duration_seconds":valid(audio_duration,0.001,3600),
            "provider_bpm":valid(bpm,20,400) if a["status"]=="complete" else None,
            "beat_count":len(a["beats"]) if isinstance(a.get("beats"),list) else None,
            "section_count":len(a["sections"]) if isinstance(a.get("sections"),list) else None,
            "aligned_word_count":valid_words if l["status"]=="complete" else None,
            "word_count":len(words) if l["status"]=="complete" else None,
            "independent_qa_required":True,"lyric_accuracy_verified":False}

def gate(rows, human_approved=False):
    """All mandatory requirements must pass; provider-only evidence cannot pass."""
    require(isinstance(rows,list) and rows,"empty requirements")
    seen=set()
    mandatory=[]
    for r in rows:
        require(isinstance(r,dict),"invalid requirement")
        k=r.get("id")
        require(isinstance(k,str) and k and k not in seen,"duplicate/invalid ID")
        seen.add(k)
        require(type(r.get("mandatory")) is bool,"mandatory flag required")
        state=r.get("status")
        require(state in ("PASS","FAIL","UNKNOWN","NOT_APPLICABLE"),"invalid result")
        if r["mandatory"]:
            require(state!="NOT_APPLICABLE","mandatory cannot be N/A")
            if state=="PASS" and r.get("source") not in ("INDEPENDENT","HUMAN"):
                state="UNKNOWN"
            mandatory.append(state)
    require(bool(mandatory),"no mandatory requirements")
    result="FAIL" if "FAIL" in mandatory else "UNKNOWN" if "UNKNOWN" in mandatory else "PASS"
    return {"overall":result,"handoff_allowed":result=="PASS" and human_approved is True}

def revision(plan_args, rows, budget, spent, upper_cost, attempts, max_attempts):
    """One-factor proposal only. No authorization, execution, or automatic retry."""
    for name,v in (("budget",budget),("spent",spent),("upper_cost",upper_cost),
                   ("attempts",attempts),("max_attempts",max_attempts)):
        integer(v,name,0,1_000_000)
    if upper_cost==0 or attempts>=max_attempts or spent+upper_cost>budget:
        return {"decision":"STOP_BUDGET_OR_LIMIT"}
    if gate(rows)["overall"]!="FAIL" or any(r["mandatory"] and r["status"]=="UNKNOWN" for r in rows):
        return {"decision":"STOP_OR_REVIEW"}
    # Only tune style adherence, and only for a confirmed independent tempo failure.
    if not any(r["id"]=="R-01" and r["mandatory"] and r["status"]=="FAIL"
               and r.get("source")=="INDEPENDENT" for r in rows):
        return {"decision":"REVIEW_NO_SUPPORTED_RULE"}
    old=plan_args.get("controls",{}).get("style_influence")
    if not number(old,0,1) or old>=1:
        return {"decision":"REVIEW_NO_SUPPORTED_STEP"}
    new=round(min(1,old+0.1),3)
    return {"decision":"PROPOSE_ONLY","change":{"field":"controls.style_influence",
            "before":old,"after":new},"requires_new_attempt_and_approval":True,
            "requires_schema_and_budget_recheck":True}

def compare_runs(runs):
    """Descriptive equal-budget run comparison; no causal/statistical claim."""
    require(isinstance(runs,list) and runs,"empty runs")
    groups={"A":[],"B":[]}
    seen=set()
    for r in runs:
        require(isinstance(r,dict) and r.get("arm") in groups,"invalid arm")
        k=r.get("run_id")
        require(isinstance(k,str) and k and k not in seen,"duplicate run")
        seen.add(k)
        budget=integer(r.get("budget"),"budget",1,1_000_000)
        spent=integer(r.get("spent"),"spent",0,budget)
        require(r.get("outcome") in ("PASS","FAIL","UNKNOWN"),"invalid outcome")
        groups[r["arm"]].append((budget,spent,r["outcome"]))
    require(all(groups.values()) and len({v[0] for g in groups.values() for v in g})==1,
            "both arms and identical run budget required")
    out={}
    for name,g in groups.items():
        passes=sum(v[2]=="PASS" for v in g)
        out[name]={"runs":len(g),"passes":passes,"unknown":sum(v[2]=="UNKNOWN" for v in g),
                   "success_rate":passes/len(g),"spent":sum(v[1] for v in g)}
    return {"mode":"DESCRIPTIVE_ONLY","arms":out,
            "success_rate_difference":out["B"]["success_rate"]-out["A"]["success_rate"],
            "causal_claim":False}

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest="command",required=True)
    e=sub.add_parser("evidence")
    for key in ("retrieve","analysis","alignment"):
        e.add_argument(key)
    g=sub.add_parser("compare"); g.add_argument("runs")
    a=p.parse_args()
    try:
        out=provider_evidence(*[read_json(getattr(a,k)) for k in ("retrieve","analysis","alignment")]) if a.command=="evidence" else compare_runs(read_json(a.runs))
        print(json.dumps(out,allow_nan=False,indent=2))
    except (ValueError,OSError,TypeError,KeyError):
        p.exit(2,"STOP: invalid evidence or contract\n")
