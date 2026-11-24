# P1 generation smoke test and reconciliation DVR

Date: 2026-11-25 JST. Authenticated Suno connector. One standard custom generation. **Generation reconciled; full independent QA and closed-loop optimization remain unverified.**

## Preconditions

- Operator authorized up to 20 song-generation credits.
- Standard text-only v6 generation: 10 credits for two songs, per [official v6 FAQ](https://help.suno.com/en/articles/13924481) and [MCP FAQ](https://suno.com/mcp).
- Account model and advanced-control grants checked. No Max Mode, media references, paid downloads, MIDI, stems or publishing.
- Synthetic Japanese lyrics, target tempo 140 BPM, soft target duration 30 s, style_influence=0.8, variety=0; one stable idempotency key. Exact song IDs, account balances, private URLs and raw responses excluded.

## Observed results

| Check | Result | Status |
|---|---|---|
| Budget authorization and standard price | 20 maximum; 10 expected for one call | PASS |
| Model and advanced controls | granted | PASS |
| Creation invocation | one invocation | PASS |
| Immediate host reply decoding | JSON decoder found additional non-whitespace text; original reply not retained by the invoking script | FAIL |
| Recovery without resend | initial finished-song search empty; later search by unique synthetic test title returned exactly two complete candidates; credit delta matched | PASS (operator reconciliation) |
| Actual song-credit consumption | 10; remaining approved budget 10 unused | PASS |
| Candidate privacy | both private in library listing | PASS |
| Model / controls metadata | both v6, style_influence=0.8, variety=0 | PASS |
| Original submitted lyrics in metadata | exact match for both; not independent sung-lyrics verification | PASS |
| Provider analysis | processing then complete for both | PASS |
| Provider lyric alignment | processing then complete; both 14/14 words marked success | PASS (alignment only) |
| WAV probe, confirm=false | both require separate download credit; no confirmation sent | PASS (safe gate) |
| Independent WAV / ASR / human acceptance | separate download authorized; signed URLs issued; binary transfer into analyzer blocked | BLOCKED |
| Closed-loop regeneration / equal-budget A/B | not executed | NOT_RUN |

Provider measurements for synthetic test songs (not independent ground truth):

| Candidate | Target BPM | Provider BPM | Absolute error BPM | Duration target s | Provider duration s | Aligned words |
|---|---:|---:|---:|---:|---:|---:|
| A | 140 | 144.6 | 4.6 | 30 | 29.6 | 14/14 |
| B | 140 | 142.2 | 2.2 | 30 | 28.8 | 14/14 |

Both fall within the illustrative SRS tempo tolerance of ±5 BPM and close to the soft duration target. This is a smoke test, not a statistical sample or proof that the controls improved generation. Provider alignment success does not establish correct sung words. Mandatory independent quality gate remains UNKNOWN. No handoff or publication.

## Incident and recovery

The connector returned mixed content that could not be parsed as a single JSON document. The script failed before retaining candidate IDs. Initial credit balance was unchanged and the finished-song library search was empty, so it was not safe to infer server-side failure. No new request was sent. Later lookup returned two completed private songs with matching test title, requested model/controls/lyrics, and a 10-credit account delta. This reconciles the original invocation operationally, but it is not a raw creation-response contract capture or an itemized billing receipt. No concurrent account operation was intentionally performed.

Required hardening: capture raw response privately before parsing, separate documented structured payload from presentation, keep an explicit SUBMISSION_UNKNOWN state until reconciliation, and never replay ambiguous paid operations automatically. A synthetic regression rejects JSON followed by arbitrary text. No undocumented host suffix is guessed. Recovery here was operator-driven in the authorized connector, not the repository CLI executing live calls.

The prior authenticated read-only DVR remains valid. Further generation was not necessary because both provider tempo measurements met the illustrative target and independent QA was unavailable. No claim of optimization superiority. Separate download consent or a manually provided local WAV is required for independent measurements.

## Follow-up: authorized WAV download (2026-11-25 JST)

The operator separately authorized two download credits for the same two private P1 candidates. Each confirmed WAV download returned status `ok`, format and an expiring signed download URL. Account reconciliation confirmed exactly two download credits consumed and no further song-generation credits consumed. The signed URLs and asset IDs are excluded from this repository.

| Check | Result |
|---|---|
| Both WAV download responses | PASS (status ok and URL present) |
| Download credit delta | PASS (2; approved maximum 2) |
| Song generation credit delta | PASS (0) |
| Transfer into independent analysis runtime | BLOCKED (private URL transfer unavailable through current runtime) |
| WAV byte hash / decode / independent BPM / duration | NOT_RUN |

The successful download response establishes authorized retrieval availability, not that this runtime has received or decoded WAV bytes. Obtain the two WAVs through the download UI and supply them directly to the analyzer in a private session; do not upload them to the public repository. No repeat paid download is necessary for this test. Do not claim independent QA or handoff acceptance until measured.

Regression CI for PR #2: [run 45429610642](https://github.com/Gacky-Lab/SUNO-GENERATION-OPTIMIZER/actions/runs/45429610642), 23 tests passed on both Python 3.11 and 3.13; merged into main. This CI used synthetic data, not actual song files.

## Follow-up: independent real WAV QA (2026-11-25 JST)

The operator supplied both downloaded WAVs directly to the private analysis runtime. Both files were decoded and measured independently of the Suno analysis. No audio, lyrics, clip identifiers, signed links or file hashes are committed. The previously blocked binary-transfer step is resolved by manual handoff, not by automated connector transfer.

| Metric | Candidate A | Candidate B |
|---|---:|---:|
| Format | PCM16 WAV, 48 kHz, stereo | PCM16 WAV, 48 kHz, stereo |
| Decoded duration (s) | 29.60 | 28.80 |
| Suno BPM | 144.6 | 142.2 |
| Independent beat-track BPM | 143.55 | 143.55 |
| Absolute difference from Suno (BPM) | 1.05 | 1.35 |
| Beat count (independent tracker) | 69 | 65 |
| Integrated loudness (LUFS) | -15.9 | -16.0 |
| Loudness range (LU) | 3.1 | 3.3 |
| True peak (dBTP) | -4.6 | -4.8 |
| Sample peak (dBFS) | -4.644 | -4.834 |
| Near-full-scale samples (absolute normalized amplitude >=32760/32768) | 0 | 0 |
| Tempo ambiguity heuristic | false | true |

The original Phase-0 pulse-only tempo heuristic returned UNKNOWN for both real songs (irregular onset intervals; approximately 7.8% and 6.7% within its interval tolerance, below its 80% criterion). This exposed a real-domain limitation, not a test failure on the synthetic click fixtures. Added `independent_qa.py` for spectral-onset beat tracking, autocorrelation alternatives, decoded duration, EBU R128 loudness and true peak. The script was run locally on both supplied WAVs. Environment: librosa 0.11.0, soundfile 0.13.1, numpy 2.3.5, scipy 1.17.0, FFmpeg 7.1.5; audio dependencies are recorded in `requirements-audio.txt` (not a full transitive lock).

For A, the strongest inspected autocorrelation candidate was 143.55 BPM (relative autocorrelation 0.468). For B, alternatives 191.41 (0.598) and 93.96 (0.590) exceeded the main 143.55 (0.523). These are periodicity candidates, not established musical tempos or calibrated confidence. Both main BPM estimates lie inside 135–145, but tempo acceptance still requires human beat confirmation. The two files decode successfully and the measured duration agrees with provider metadata. No near-full-scale samples were found; this does not prove absence of distortion or mastering defects. Loudness and peak are descriptive; no streaming-platform target is imposed.

| DVR follow-up | Result |
|---|---|
| Manual binary handoff and WAV decode | PASS (2/2) |
| Independent duration and provider agreement | PASS (2/2; exact displayed duration) |
| Independent BPM estimator execution | PASS (2/2); main estimates in target band |
| Mandatory tempo acceptance | UNKNOWN (human verification pending; B ambiguity) |
| Loudness and peak measurement | PASS (measurement obtained; no quality threshold implied) |
| Independent sung-lyric accuracy / author approval | NOT_RUN |
| Closed-loop regeneration, baseline comparison, downstream handoff | NOT_RUN |

Reproduce locally with Python and FFmpeg installed: `python -m pip install -r requirements-audio.txt`, then `python independent_qa.py local/candidate.wav`. No network or Suno operations in the analyzer. Existing 23-case CI covers the prior core; this newly added optional analyzer was executed on the actual WAVs locally, not yet covered by GitHub Actions. Two songs from a single generation call cannot establish optimization superiority. The full mandatory quality gate remains UNKNOWN.
