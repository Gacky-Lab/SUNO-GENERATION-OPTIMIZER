"""Reproduce the descriptive P2 pilot results. No live calls or audio acceptance."""
import json
import math
import sys
from pathlib import Path

def summarize(data):
    rows=data["rows"]
    expected={"A1":"A","B1":"B","B2":"B","A2":"A","INT1":"I"}
    if len(rows)!=10 or len({r["candidate"] for r in rows})!=10:
        raise ValueError("expected ten distinct candidates")
    if any(r["call"] not in expected or r["arm"]!=expected[r["call"]] for r in rows):
        raise ValueError("invalid call/arm")
    if any(sum(r["call"]==call for r in rows)!=2 for call in expected):
        raise ValueError("two candidates per call required")
    if data["observed_credit_delta"]!=len(expected)*data["credits_per_call"]:
        raise ValueError("credit mismatch")
    for r in rows:
        if r["source"]!="SUNO_PROVIDER_NOT_INDEPENDENT":
            raise ValueError("unexpected evidence source")
        if r["style_influence"]!=(data["intervention_style_influence"] if r["arm"]=="I" else data["initial_style_influence"]):
            raise ValueError("unexpected control value")
    def known(v):
        return type(v) in (int,float) and math.isfinite(v)
    def passed(r):
        return r["status"]=="complete" and known(r["bpm"]) and known(r["duration_s"]) and abs(r["bpm"]-data["target_bpm"])<=data["tolerance_bpm"] and data["min_duration_s"]<=r["duration_s"]<=data["max_duration_s"]
    def stats(group):
        errors=[abs(r["bpm"]-data["target_bpm"]) for r in group if r["status"]=="complete" and known(r["bpm"])]
        n=sum(passed(r) for r in group)
        return {"candidates":len(group),"pass":n,"pass_rate":n/len(group),"mae_bpm_known":round(sum(errors)/len(errors),4) if errors else None,"known_tempo":len(errors)}
    b1=[r for r in rows if r["call"]=="B1"]
    return {"A":stats([r for r in rows if r["arm"]=="A"]),
            "B":stats([r for r in rows if r["arm"]=="B"]),
            "fixed_all":stats([r for r in rows if r["arm"]!="I"]),
            "B1":stats(b1),"intervention":stats([r for r in rows if r["arm"]=="I"]),
            "adaptive_triggered_in_v1":all(r["status"]=="complete" and known(r["bpm"]) and known(r["duration_s"]) for r in b1) and not any(passed(r) for r in b1),
            "independent_acceptance":"UNKNOWN","causal_claim":False}
if __name__=="__main__":
    print(json.dumps(summarize(json.loads(Path(sys.argv[1]).read_text())),indent=2,allow_nan=False))
