"""Optional audio tests; mandatory in the audio CI job."""
import importlib.util
import os
import shutil
import tempfile
import unittest
from pathlib import Path

deps = all(importlib.util.find_spec(x) is not None for x in ("numpy","scipy","librosa","soundfile"))
available = deps and bool(shutil.which("ffmpeg"))
if os.environ.get("SGO_REQUIRE_AUDIO")=="1" and not available:
    raise RuntimeError("mandatory audio dependencies missing")

@unittest.skipUnless(available,"optional audio dependencies not installed")
class IndependentAudioTests(unittest.TestCase):
    def measure_click(self,bpm):
        import numpy as np
        import soundfile as sf
        from independent_qa import measure
        sr=22050
        samples=np.zeros(sr*12)
        if bpm:
            for t in np.arange(.1,11.8,60/bpm):
                i=int(t*sr)
                n=int(.025*sr)
                samples[i:i+n]=.5*np.sin(2*np.pi*800*np.arange(n)/sr)*np.hanning(n)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"synthetic.wav"
            sf.write(p,samples,sr,subtype="PCM_16")
            return measure(p)
    def test_known_click_tempos(self):
        for bpm in (120,140):
            with self.subTest(bpm=bpm):
                r=self.measure_click(bpm)
                self.assertAlmostEqual(r["tempo_bpm"],bpm,delta=2)
                self.assertAlmostEqual(r["duration_seconds"],12,delta=.1)
                self.assertEqual(r["near_full_scale_samples"],0)
                self.assertFalse(r["handoff_allowed"])
                self.assertTrue(r["tempo_requires_human_confirmation"])
    def test_silence_unknown(self):
        r=self.measure_click(None)
        self.assertTrue(r["silence"])
        for key in ("tempo_bpm","integrated_lufs","true_peak_dbtp","sample_peak_dbfs","rms_dbfs"):
            self.assertIsNone(r[key])
        self.assertTrue(r["tempo_ambiguity_review"])
        self.assertFalse(r["handoff_allowed"])
