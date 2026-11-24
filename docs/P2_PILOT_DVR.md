# P2 provider-feedback pilot DVR (2026-11-25 JST)

## Scope and actual consumption

Operator authorized appropriate use. [Protocol v1](P2_PILOT_PROTOCOL.md) was committed before the four-call pilot; a [separate intervention protocol](P2_INTERVENTION_PROTOCOL.md) was committed before the fifth call. Five standard v6 calls, two candidates each, all ten completed and private. Observed song-credit delta 50, download-credit delta 0. No Max Mode, downloads, MIDI, stems, publication or automatic handoff.

All creation calls returned mixed host text. The first line supplied tentative candidate IDs only; each pair was verified with audio-wait, unique-title library search, model/controls metadata and the observed 10-credit delta before the next call. No replay. Raw responses and private IDs/URLs are excluded. The repository code did not execute live calls autonomously; the authorized connector was operated by the assistant.

## Results

175 BPM ±5 and 25–45 s; target duration 35 s. Provider analysis complete for all ten.

| Call | style_influence | BPM (both candidates) | Duration s | Endpoint pass |
|---|---:|---|---|---:|
| A1 | 0.4 | 176.0, 174.7 | 34.72, 34.60 | 2/2 |
| B1 | 0.4 | 136.0, 178.7 | 34.40, 34.80 | 1/2 |
| B2 | 0.4 | 174.0, 175.0 | 34.48, 34.56 | 2/2 |
| A2 | 0.4 | 179.0, 175.8 | 35.00, 34.20 | 2/2 |
| INT1 (separate) | 0.5 | 180.9, 178.0 | 34.92, 35.56 | 1/2 |

V1 adaptive trigger did NOT fire because B1 had one acceptable candidate. A and B were therefore both fixed-control arms; A 4/4, B 3/4. All eight fixed candidates: 7/8 (87.5%), mean absolute BPM error 6.225. B1: 1/2, mean absolute error 21.35 BPM. The separate one-factor intervention: 1/2, mean absolute error 4.45 BPM. The intervention changed the requested control and returned both matching metadata values, but did not improve pass rate over B1. The reduced mean error is not causal evidence (selection on an outlier, regression to mean, stochastic variation). No superiority claim. Two correlated candidates per call; no independent replications sufficient for inference.

## Reproduction and remaining gates

Run `python p2_pilot.py fixtures/p2_pilot_provider_results.json`. The redacted dataset contains provider measurements of synthetic test songs, not independent ground truth. The v1 all-fail trigger may be insufficient for candidate-level objectives; any new policy and metric must be specified before a fresh, replicated comparison. No post-hoc change to v1. Independent audio QA, lyric accuracy, author approval, and full closed-loop efficacy remain UNKNOWN/NOT_RUN. No further credits used for this pilot.

The separate intervention demonstrates an operator-directed provider-feedback action through the actual connector, not the independent production policy or autonomous execution of the Python optimizer. No statistical confidence intervals are presented because one run per arm cannot establish a reliable treatment effect.
