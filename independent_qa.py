"""Independent local PCM16 WAV evidence; no network or Suno calls."""
import argparse
import json
import math
import re
import subprocess
from pathlib import Path


def measure(path):
    import librosa
    import numpy as np
    import soundfile as sf
    from scipy.signal import find_peaks
    p = Path(path)
    info = sf.info(p)
    if (p.stat().st_size > 256*1024*1024 or info.format != 'WAV'
            or info.subtype != 'PCM_16' or info.channels not in (1,2)
            or not 8000 <= info.samplerate <= 96000 or not 0 < info.duration <= 600):
        raise ValueError('unsupported WAV')
    y,sr = sf.read(p, always_2d=True)
    if len(y) != info.frames or not np.isfinite(y).all():
        raise ValueError('invalid decoded samples')
    mono = librosa.resample(y.mean(axis=1), orig_sr=sr, target_sr=22050)
    hop = 256
    onset = librosa.onset.onset_strength(y=mono,sr=22050,hop_length=hop)
    tempo,beats = librosa.beat.beat_track(onset_envelope=onset,sr=22050,hop_length=hop)
    ac = librosa.autocorrelate(onset-onset.mean(),max_size=round(22050/hop*2))
    peaks = [i for i in find_peaks(ac)[0] if 60 <= 60*22050/hop/i <= 200]
    peaks = sorted(peaks,key=lambda i:ac[i],reverse=True)[:5] if ac[0]>0 else []
    alternatives = [{'bpm':round(float(60*22050/hop/i),2), 'relative_ac':round(float(ac[i]/ac[0]),3)} for i in peaks]
    t = float(np.asarray(tempo).reshape(-1)[0]) if len(beats)>=5 else None
    if t is not None and (not math.isfinite(t) or t<=0):
        t=None
    # A heuristic ambiguity indicator, not calibrated confidence. Any stronger
    # non-octave periodicity than the nearest main-period candidate needs review.
    ambiguous = True
    if t is not None and alternatives:
        nearest=min(alternatives,key=lambda a:abs(a['bpm']-t))
        ambiguous=abs(nearest['bpm']-t)>3 or any(a['relative_ac']>nearest['relative_ac'] and min(abs(a['bpm']-t),abs(a['bpm']-t/2),abs(a['bpm']-t*2))>3 for a in alternatives)
    log = subprocess.run(['ffmpeg','-nostdin','-hide_banner','-nostats','-i',str(p.resolve()),'-af','ebur128=peak=true','-f','null','-'],capture_output=True,text=True,check=True,timeout=120).stderr
    summary=log.rsplit('Summary:',1)[-1]
    def metric(pattern):
        m=re.search(pattern,summary)
        if not m: raise ValueError('missing loudness metric')
        v=float(m.group(1))
        return v if math.isfinite(v) else None
    peak=float(np.abs(y).max()); rms=float(np.sqrt(np.mean(y*y)))
    return {'source':'INDEPENDENT_WAV','sample_rate':sr,'channels':info.channels,'subtype':info.subtype,
            'duration_seconds':len(y)/sr,'tempo_bpm':round(t,2) if t is not None else None,'beat_count':len(beats),
            'tempo_ambiguity_review':ambiguous,'tempo_alternatives':alternatives,'tempo_requires_human_confirmation':True,
            'integrated_lufs':metric(r'I:\s+(-?[\d.]+) LUFS'), 'lra_lu':metric(r'LRA:\s+(-?[\d.]+) LU'),
            'true_peak_dbtp':metric(r'Peak:\s+(-?[\d.]+) dBFS'),
            'sample_peak_dbfs':round(20*math.log10(peak),3) if peak>0 else None,
            'rms_dbfs':round(20*math.log10(rms),3) if rms>0 else None,
            'near_full_scale_samples':int(np.sum(np.abs(y)>=32760/32768)),
            'lyric_accuracy_verified':False,'handoff_allowed':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('wav'); a=p.parse_args()
    try:
        print(json.dumps(measure(a.wav),indent=2,allow_nan=False))
    except (ValueError,RuntimeError,OSError,subprocess.SubprocessError):
        p.exit(2,'STOP: invalid or unsupported audio / analysis failure\n')
