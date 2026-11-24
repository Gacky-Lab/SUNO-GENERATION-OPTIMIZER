import json
import unittest
from pathlib import Path
from p2_pilot import summarize

class PilotTest(unittest.TestCase):
    def data(self):
        return json.loads((Path(__file__).resolve().parents[1]/"fixtures/p2_pilot_provider_results.json").read_text())
    def test_actual_redacted_results(self):
        r=summarize(self.data())
        self.assertEqual(r["fixed_all"]["pass"],7)
        self.assertEqual(r["A"]["pass"],4)
        self.assertEqual(r["B"]["pass"],3)
        self.assertEqual(r["intervention"]["pass"],1)
        self.assertAlmostEqual(r["intervention"]["mae_bpm_known"],4.45)
        self.assertFalse(r["adaptive_triggered_in_v1"])
        self.assertFalse(r["causal_claim"])
    def test_missing_counts_as_nonpass(self):
        d=self.data()
        d["rows"][0]["bpm"]=None
        r=summarize(d)
        self.assertEqual(r["fixed_all"]["pass"],6)
        self.assertEqual(r["fixed_all"]["candidates"],8)
    def test_bad_cost_or_duplicate(self):
        d=self.data()
        d["observed_credit_delta"]=40
        with self.assertRaises(ValueError): summarize(d)
        d=self.data()
        d["rows"][0]["candidate"]=d["rows"][1]["candidate"]
        with self.assertRaises(ValueError): summarize(d)
