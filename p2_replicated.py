"""Descriptive paired-block analysis. Provider data are not independent QA."""
import json
import math
import sys
from pathlib import Path

def summarize(data):
    rows=data["rows"]
    targets={"v2":{"01":175,"02":95,"03":155},"v3":{"01":175,"02":95}}
    if len(rows)!=26 or len({r["candidate"] for r in rows})!=26:
        raise ValueError("26 distinct candidates required")
    if (data["tempo_tolerance"],data["duration_min"],data["duration_max"],data["credits_per_call"])!=(5,25,45,10):
        raise ValueError("protocol thresholds changed")
    if data["observed_credits"]!={"v2":90,"v3":40}:
        raise ValueError("cost mismatch")
    def known(v):
        return type(v) in (int,float) and math.isfinite(v)
    def pass_(r):
        return r["status"]=="complete" and known(r["bpm"]) and known(r["duration_s"]) and abs(r["bpm"]-r["target"])<=5 and 25<=r["duration_s"]<=45
    def stats(g):
        errs=[abs(r["bpm"]-r["target"]) for r in g if r["status"]=="complete" and known(r["bpm"])]
        return {"candidates":len(g),"pass":sum(map(pass_,g)),"pass_rate":sum(map(pass_,g))/len(g),"mae_bpm":round(sum(errs)/len(errs),4) if errs else None,"missing_tempo":len(g)-len(errs)}
    if any(r["source"]!="SUNO_PROVIDER_NOT_INDEPENDENT" or r["study"] not in targets or r["block"] not in targets[r["study"]] or r["target"]!=targets[r["study"]][r["block"]] for r in rows):
        raise ValueError("invalid study/block/evidence")
    out={}
    for study,blocks in targets.items():
        g=[r for r in rows if r["study"]==study]
        paired=[]
        for block,target in blocks.items():
            q=[r for r in g if r["block"]==block]
            arms=("I","A","B") if study=="v2" else ("A","B")
            if len(q)!=2*len(arms) or any(sum(r["arm"]==a for r in q)!=2 for a in arms):
                raise ValueError("call count mismatch")
            a,b=([r for r in q if r["arm"]==arm] for arm in ("A","B"))
            initial=[r for r in q if r["arm"]=="I"]
            if study=="v2" and any(r["status"]!="complete" or not known(r["bpm"]) or not known(r["duration_s"]) for r in initial):
                raise ValueError("initial evidence unknown: follow-ups not authorized")
            changed=study=="v3" or not all(map(pass_,initial))
            for r in q:
                if r["style_influence"]!=(.5 if r["arm"]=="B" and changed else .4):
                    raise ValueError("control/protocol mismatch")
            paired.append({"block":block,"target":target,"intervention":changed,"A_pass":sum(map(pass_,a)),"B_pass":sum(map(pass_,b)),"B_minus_A":sum(map(pass_,b))-sum(map(pass_,a))})
        out[study]={"A":stats([r for r in g if r["arm"]=="A"]),"B":stats([r for r in g if r["arm"]=="B"]),"all":stats(g),"paired":paired,"intervention_blocks":sum(p["intervention"] for p in paired)}
    return {"studies":out,"independent_acceptance":"UNKNOWN","causal_claim":False}

if __name__=="__main__":
    print(json.dumps(summarize(json.loads(Path(sys.argv[1]).read_text())),indent=2,allow_nan=False))
