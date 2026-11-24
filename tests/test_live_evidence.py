import json
import unittest
from live_evidence import provider_evidence, wait_summary, gate, revision, compare_runs
from suno_optimizer import ContractError

def env(data):
    return {"text":json.dumps(data)}

def row(state="PASS",source="INDEPENDENT"):
    return {"id":"R-01","mandatory":True,"status":state,"source":source}

def evidence():
    return [env({"id":"mock","status":"complete","metadata":{"duration":42,"lyrics":"secret"},"song_url":"https://example.invalid"}),
            env({"audio_id":"mock","status":"complete","bpm":140,"duration_s":42,"beats":[{}],"sections":[{}]}),
            env({"audio_id":"mock","status":"complete","words":[{"word":"secret","start_s":0,"end_s":1,"success":True},{"success":False}]})]

class LiveEvidenceTest(unittest.TestCase):
    def test_evidence_redacted(self):
        out=provider_evidence(*evidence())
        self.assertEqual(out["provider_bpm"],140)
        self.assertEqual(out["aligned_word_count"],1)
        self.assertFalse(out["lyric_accuracy_verified"])
        self.assertNotIn("secret",json.dumps(out))
        self.assertNotIn("mock",json.dumps(out))
    def test_partial(self):
        r,a,l=evidence()
        a=env({"audio_id":"mock","status":"processing","bpm":140})
        self.assertIsNone(provider_evidence(r,a,l)["provider_bpm"])
    def test_wrong_id(self):
        r,a,l=evidence()
        with self.assertRaises(ContractError):
            provider_evidence(r,a,env({"audio_id":"other","status":"complete","words":[]}))
    def test_wait(self):
        result=env({"clips":[{"id":"a","status":"complete"},{"id":"b","error":"failure"}]})
        self.assertEqual(wait_summary(result,["a","b"])["error_count"],1)
        with self.assertRaises(ContractError): wait_summary(result,["b","a"])
    def test_gate(self):
        self.assertFalse(gate([row()],False)["handoff_allowed"])
        self.assertTrue(gate([row()],True)["handoff_allowed"])
        self.assertEqual(gate([row(source="SUNO_PROVIDER_NOT_INDEPENDENT")])["overall"],"UNKNOWN")
        self.assertEqual(gate([row("FAIL")])["overall"],"FAIL")
        with self.assertRaises(ContractError): gate([row(),row()])
    def test_revision(self):
        args={"lyrics":"unchanged","controls":{"style_influence":0.8}}
        out=revision(args,[row("FAIL")],20,10,10,1,2)
        self.assertEqual(out["change"]["after"],0.9)
        self.assertEqual(args["controls"]["style_influence"],0.8)
        self.assertEqual(revision(args,[row("FAIL")],19,10,10,1,2)["decision"],"STOP_BUDGET_OR_LIMIT")
        self.assertEqual(revision(args,[row("UNKNOWN")],20,10,10,1,2)["decision"],"STOP_OR_REVIEW")
    def test_compare(self):
        a={"run_id":"1","arm":"A","budget":20,"spent":10,"outcome":"UNKNOWN"}
        b={"run_id":"2","arm":"B","budget":20,"spent":20,"outcome":"PASS"}
        self.assertEqual(compare_runs([a,b])["success_rate_difference"],1)
        self.assertFalse(compare_runs([a,b])["causal_claim"])
        with self.assertRaises(ContractError): compare_runs([a,dict(b,budget=30)])

if __name__=="__main__":
    unittest.main()
