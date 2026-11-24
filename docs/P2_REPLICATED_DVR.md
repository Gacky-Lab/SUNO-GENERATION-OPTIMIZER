# P2 v2 / v3 additional verification DVR — 2026-11-25 JST

## Scope and budget

The operator authorized additional credit usage. [V2 protocol](P2_V2_PROTOCOL.md) was committed before any v2 generation; [v3 protocol](P2_V3_PROTOCOL.md) before any v3 generation. These are distinct exploratory studies, not one randomized efficacy trial. V2: 9 calls / 18 completed private songs / 90 song credits. V3: 4 calls / 8 completed private songs / 40 song credits. Total additional: 13 calls, 26 songs, 130 song credits, zero paid downloads. No Max Mode, references, publication, or automatic handoff. Each pair was checked against its unique title, candidate IDs, model, controls, completion/privacy and account delta before proceeding. One v2 call's account balance was initially unchanged; generation was paused until subsequent reads reconciled the 10-credit delta and both candidates. No replay. A read batch hit a host tool-call limit after already reconciled submissions; remaining measurements were retrieved in a separate read batch. The official authorized connector was operated by the assistant; not a standalone Python live client.

## V2: repeated same-condition behavior, provider measurements

| Block target | Initial BPM | A follow-up BPM | B follow-up BPM | Initial passes | A passes | B passes | Total |
|---|---|---|---|---:|---:|---:|---:|
| 175 | 177.0 / 179.2 | 136.3 / 132.2 | 130.6 / 139.6 | 2/2 | 0/2 | 0/2 | 2/6 |
| 95 | 96.5 / 96.1 | 133.9 / 94.9 | 96.1 / 95.5 | 2/2 | 1/2 | 2/2 | 5/6 |
| 155 | 155.9 / 155.4 | 158.3 / 153.2 | 154.3 / 155.3 | 2/2 | 2/2 | 2/2 | 6/6 |

All shared initial candidates passed; **no adaptive trigger fired**. All v2 calls therefore used style_influence 0.4. Total 13/18 (72.2%). Follow-ups A 3/6, B 4/6; their difference is not an intervention effect. Large provider-measured outliers occurred even after initial success. Different lyric sets accompany different tempo targets; no intrinsic tempo-difficulty inference is justified.

## V3: separate matched intervention, conditional on observed failures

| Target | A: 0.4 BPM | B: 0.5 BPM | A passes | B passes |
|---|---|---|---:|---:|
| 175 | 175.6 / 137.2 | 136.1 / 134.5 | 1/2 | 0/2 |
| 95 | 97.5 / 94.4 | 96.2 / 95.8 | 2/2 | 2/2 |
| Total | | | 3/4 (75%) | 2/4 (50%) |

Equal 20-credit arm costs, A mean absolute BPM error 10.375, B 20.35. The parameter was actually changed and metadata confirmed. All 26 durations in v2/v3 within 25–45 s. The observed results do not support superiority of this one-factor rule. No significance inference from two paired blocks, correlated candidates, selection on prior failure and uncertain provider BPM measurements. Do not pool the studies to infer a treatment effect. H1 remains unresolved; the specific tested rule should not be promoted as a proven improvement. Negative result retained. An appropriate next study would preregister an alternative mechanism and use independent measurements and call/block-level replication.

## Independent QA and automation boundaries

The paid songs in this study were not downloaded. A new signed URL for an already-paid P1 WAV was obtained without extra charge, but direct transfer into the independent runtime was rejected by its access gate. Signed URLs were not submitted to a public search or committed. P1 two-song WAV measurements remain the only independent real-audio evidence. No raw private IDs or links in Git.

Reproduction: `python p2_replicated.py fixtures/p2_replicated_provider_results.json`. This includes all 26 provider observations, both studies separately, and checks for control/cost/endpoint consistency. New offline helpers in verification.py cover normalized transcript CER and a single-writer atomic checkpoint with exact approval fingerprint, budget/call/candidate/time admission and fail-closed SUBMISSION_UNKNOWN recovery. They require operator-supplied evidence and do not execute live network calls. Actual sung-lyric recognition/pronunciation is unverified. The independent analyzer was found to fail on silence during a synthetic local check; its handling was patched and audio regression tests added. No claim of complete SRS coverage or automatic acceptance.

## Current conclusion

- Practical external generation, readback, operator-directed one-factor changes, provider QA, budget reconciliation and prior two-WAV independent measurement are demonstrated.
- H1: no positive efficacy evidence. H2: human confirmation burden not measured. H3: partial traceability demonstrated; no deterministic generation guarantee.
- Full independent P2 quality gate, real ASR/human lyric accuracy, live autonomous integration, raw MCP schema export, downstream handoff and optional P3 capabilities remain unverified or out of this scope.
