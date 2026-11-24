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
