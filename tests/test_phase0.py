import copy
import hashlib
import json
import math
import struct
import tempfile
import unittest
import wave
from pathlib import Path

import suno_optimizer as s

ROOT = Path(__file__).resolve().parents[1]

def pages():
    return json.loads((ROOT/"fixtures/mcp_observed_subset.mock.json").read_text())

def handoff():
    text = "夜明けを待つ\n光を探す\n"
    return {"contract_version":"1.0.0","song_id":"synthetic","lyric_version_id":"v1",
            "language":"ja","lyrics_text":text,"lyrics_sha256":hashlib.sha256(text.encode()).hexdigest()}

def plan(snapshot=None, **changes):
    kwargs = dict(snapshot=snapshot or s.tools_snapshot(pages()), handoff=handoff(),
                  style="electronic rock", bpm=140, duration=30, run_id="offline-1",
                  approved_credits=20, estimated_upper=10, remaining=30,max_candidates=2)
    kwargs.update(changes)
    return s.plan_create(**kwargs)

def clip_wav(path, bpm=None):
    rate=16000
    with wave.open(str(path),"wb") as w:
        w.setparams((1,2,rate,0,"NONE","not compressed"))
        samples=[]
        for i in range(rate*12):
            t=i/rate
            pulse=bpm is not None and t>=.1 and (t-.1)%(60/bpm)<.025
            samples.append(int(16000*math.sin(2*math.pi*800*t)) if pulse else 0)
        w.writeframes(struct.pack("<"+"h"*len(samples),*samples))

class TestContract(unittest.TestCase):
    def test_snapshot(self):
        p=pages(); snap=s.tools_snapshot(p)
        self.assertFalse(snap["missing"])
        self.assertEqual(snap["schema_sha256"],s.tools_snapshot(p)["schema_sha256"])
    def test_pagination(self):
        p=pages(); p[0]["nextCursor"]="next"
        with self.assertRaises(s.ContractError): s.tools_snapshot(p)
    def test_duplicate_tool(self):
        p=pages(); p[0]["tools"].append(p[0]["tools"][0])
        with self.assertRaises(s.ContractError): s.tools_snapshot(p)
    def test_plan_is_not_call(self):
        a=plan(); b=plan()
        self.assertEqual(a,b)
        self.assertEqual(a["execution"],"PROPOSAL_ONLY")
        self.assertEqual(a["call"]["arguments"]["lyrics"],handoff()["lyrics_text"])
        self.assertIn("140 BPM",a["call"]["arguments"]["style"])
        self.assertNotIn("clip_count",a["call"]["arguments"])
        self.assertNotEqual(a["call"]["arguments"]["idempotency_key"],
                            plan(run_id="offline-2")["call"]["arguments"]["idempotency_key"])
    def test_schema_change_stops(self):
        p=pages()
        for tool in p[0]["tools"]:
            if tool["name"]=="audio-create": del tool["inputSchema"]["properties"]["duration_strict"]
        with self.assertRaises(s.ContractError): plan(s.tools_snapshot(p))
    def test_unobserved_argument(self):
        with self.assertRaises(s.ContractError):
            s.proposed_call(s.tools_snapshot(pages()),"audio-create",{"clip_count":1})
    def test_remote_ref_rejected(self):
        with self.assertRaises(s.ContractError): s.schema_check({"$ref":"https://example.org/schema"}, {})
    def test_budget(self):
        for k,v in [("approved_credits",9),("remaining",9),("estimated_upper",None),
                    ("estimated_upper",True),("max_candidates",1)]:
            with self.subTest(k=k), self.assertRaises(s.ContractError): plan(**{k:v})
    def test_lyric_hash(self):
        h=handoff(); h["lyrics_text"]=h["lyrics_text"].replace("\n","\r\n")
        self.assertEqual(s.lyric_text(h),handoff()["lyrics_text"])
        h["lyrics_text"]+="x"
        with self.assertRaises(s.ContractError): plan(handoff=h)
    def test_limits(self):
        with self.assertRaises(s.ContractError): plan(duration=361)
        with self.assertRaises(s.ContractError): plan(style="a"*1000)
    def test_multiple_ids(self):
        result={"structuredContent":{"clip_ids":["mock-a","mock-b"]}}
        self.assertEqual(s.candidate_ids(result,2),["mock-a","mock-b"])
        with self.assertRaises(s.ContractError): s.candidate_ids(result,1)
        calls=s.wait_calls(s.tools_snapshot(pages()),[str(i) for i in range(13)])
        self.assertEqual([len(c["arguments"]["ids"]) for c in calls],[12,1])
        self.assertTrue(all(c["arguments"]["until"]=="complete" for c in calls))
    def test_error_and_prose(self):
        for r in [{"isError":True,"structuredContent":{"clip_ids":["a"]}},
                  {"content":[{"type":"text","text":"looks good"}]},
                  {"structuredContent":{"clip_ids":["a","a"]}}]:
            with self.assertRaises(ValueError): s.candidate_ids(r,2)
    def test_download(self):
        self.assertFalse(s.download_probe(s.tools_snapshot(pages()),"mock-a")["arguments"]["confirm"])
        self.assertEqual(s.download_decision({"structuredContent":{"status":"requires_credit"}}),
                         "NEEDS_SEPARATE_APPROVAL")
        self.assertEqual(s.download_decision({"structuredContent":{"status":"processing"}}),
                         "WAIT_FOR_DOWNLOAD")
    def test_current_connector_contract(self):
        a=plan(model="v6",allowed_models=["v6"],controls={"style_influence":0.8,"variety":0},advanced=True)
        self.assertEqual(a["call"]["arguments"]["model"],"v6")
        self.assertEqual(a["call"]["arguments"]["controls"]["variety"],0)
        for kw in ({"model":"v6","allowed_models":[]},
                   {"controls":{"weirdness":0.5}},
                   {"controls":{"audio_influence":0.5},"advanced":True},
                   {"controls":{"variety":True},"advanced":True}):
            with self.assertRaises(s.ContractError): plan(**kw)
        self.assertEqual(s.candidate_ids({"text":json.dumps({"clip_ids":["a","b"]})},2),["a","b"])
    def test_mixed_creation_reply_stops(self):
        raw = {"text": json.dumps({"clip_ids":["mock-a","mock-b"]}) + "\nAdditional host output"}
        with self.assertRaises(ValueError):
            s.candidate_ids(raw,2)
    def test_wav(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"x.wav"
            for bpm in (120,140):
                clip_wav(p,bpm); m=s.wav_metrics(p)
                self.assertAlmostEqual(m["duration_seconds"],12,places=2)
                self.assertAlmostEqual(m["tempo_bpm"],bpm,delta=2)
                self.assertEqual(s.evaluate(m,bpm,5,11,13)["overall"],"UNKNOWN")
                self.assertEqual(s.evaluate(m,bpm,5,11,13,True)["overall"],"PASS")
                self.assertEqual(s.evaluate(m,bpm,5,20,30,True)["overall"],"FAIL")
            clip_wav(p); self.assertIsNone(s.wav_metrics(p)["tempo_bpm"])

if __name__=="__main__":
    unittest.main()
