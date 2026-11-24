import tempfile
import unittest
from pathlib import Path
from verification import lyric_cer,new_run,reserve,reconcile,totals,save_checkpoint,load_checkpoint
from suno_optimizer import ContractError
F="a"*64
class VerificationTest(unittest.TestCase):
    def test_cer(self):
        self.assertEqual(lyric_cer("[Verse]\n夜明け、光","夜明け 光",True)["cer"],0)
        self.assertEqual(lyric_cer("あいう","あう",True)["edit_distance"],1)
        self.assertEqual(lyric_cer("あいう","あえう",True)["edit_distance"],1)
        self.assertEqual(lyric_cer("あ","あいう",True)["cer"],2)
        self.assertEqual(lyric_cer("あ","あ")["status"],"UNKNOWN")
        self.assertEqual(lyric_cer("あ",None,True)["status"],"UNKNOWN")
        self.assertEqual(lyric_cer("","",True)["status"],"UNKNOWN")
        self.assertEqual(lyric_cer("あ","",True)["status"],"FAIL")
    def test_resume_blocks_replay(self):
        r=new_run(20,2,4,60)
        r=reserve(r,"a",F,F,10,2,0,100)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"private.json"
            save_checkpoint(p,r); r=load_checkpoint(p)
            self.assertEqual(totals(r)["reserved"],10)
            with self.assertRaises(ContractError): reserve(r,"b",F,F,10,2,1,90)
            with self.assertRaises(ContractError): reconcile(r,"a",["x"],10,True)
            with self.assertRaises(ContractError): reconcile(r,"a",["x","y"],10,False)
            r=reconcile(r,"a",["x","y"],10,True)
            save_checkpoint(p,r); self.assertEqual(load_checkpoint(p),r)
        with self.assertRaises(ContractError): reserve(r,"a",F,F,10,2,1,90)
        r=reserve(r,"b",F,F,10,2,1,90)
        with self.assertRaises(ContractError): reconcile(r,"b",["x","z"],10,True)
        r=reconcile(r,"b",["z","w"],10,True)
        self.assertEqual(totals(r)["spent"],20)
        with self.assertRaises(ContractError): reserve(r,"c",F,F,10,2,2,80)
    def test_admission_limits(self):
        r=new_run(10,1,2,60)
        for args in (("a",F,"b"*64,10,2,0,100),("a",F,F,None,2,0,100),("a",F,F,11,2,0,100),
                     ("a",F,F,10,3,0,100),("a",F,F,10,2,60,100),("a",F,F,10,2,0,9)):
            with self.subTest(args=args), self.assertRaises(ContractError): reserve(r,*args)
