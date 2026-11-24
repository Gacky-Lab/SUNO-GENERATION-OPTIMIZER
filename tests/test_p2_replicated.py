import copy
import json
import unittest
from pathlib import Path
from p2_replicated import summarize
class ReplicatedTests(unittest.TestCase):
    def data(self):
        return json.loads((Path(__file__).resolve().parents[1]/"fixtures/p2_replicated_provider_results.json").read_text())
    def test_actual_redacted_results(self):
        result=summarize(self.data())
        v2,v3=(result["studies"][s] for s in ("v2","v3"))
        self.assertEqual(v2["all"]["pass"],13)
        self.assertEqual(v2["A"]["pass"],3)
        self.assertEqual(v2["B"]["pass"],4)
        self.assertEqual(v2["intervention_blocks"],0)
        self.assertEqual(v3["A"]["pass"],3)
        self.assertEqual(v3["B"]["pass"],2)
        self.assertAlmostEqual(v3["A"]["mae_bpm"],10.375)
        self.assertAlmostEqual(v3["B"]["mae_bpm"],20.35)
        self.assertFalse(result["causal_claim"])
    def test_missing_initial_stops(self):
        d=self.data(); d["rows"][0]["bpm"]=None
        with self.assertRaises(ValueError): summarize(d)
    def test_changed_control_or_cost_rejected(self):
        d=self.data(); d["rows"][2]["style_influence"]=.5
        with self.assertRaises(ValueError): summarize(d)
        d=self.data(); d["observed_credits"]["v3"]=30
        with self.assertRaises(ValueError): summarize(d)
    def test_missing_followup_counts_as_nonpass(self):
        d=self.data(); d["rows"][-1]["bpm"]=None
        r=summarize(d)["studies"]["v3"]["A"]
        self.assertEqual(r["pass"],2)
        self.assertEqual(r["candidates"],4)
        self.assertEqual(r["missing_tempo"],1)
