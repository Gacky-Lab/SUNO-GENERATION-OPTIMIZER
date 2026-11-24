# Phase-0: MCP contract planner / independent WAV QA

Date: 2026-11-25 JST. **Partial offline implementation. Subsequent authenticated read-only connector tests are recorded in [the current DVR](AUTHENTICATED_INTERFACE_DVR.md); no paid generation performed.** This is a small executable research baseline, not the full optimizer.

## 1. Evidence levels

- Official: [connection instructions](https://help.suno.com/en/articles/14551425), [capabilities](https://help.suno.com/en/articles/14551361), [FAQ](https://help.suno.com/en/articles/14486145), [MCP beta](https://suno.com/release-notes/suno-mcp-beta).
- Observed by a third party, not guaranteed for this account: [WillMakes, 2026-10-30/31 tool observations](https://github.com/WillMakes/ai-music-maker/blob/main/docs/suno-mcp.md).
- Local test fixture: fixtures/mcp_observed_subset.mock.json is a deliberately reduced, independently authored input-schema example; NOT a server capture. It must never be used as proof of account capability.
- Authenticated read-only connector declarations and responses have now been inspected; see the current DVR. Raw tools/list export, actual generation cost and paid calls remain NOT_RUN.

## 2. Actual interface mapping

| Capability | Third-party observed wire name | Initial implementation |
|---|---|---|
| Credits | account-usage | Discover capability; operator checks current plan, credit limits and cost |
| Custom generation | audio-create | Build lyrics/style/duration/duration_strict/idempotency_key proposal against supplied schema; BPM remains a style instruction |
| Multiple candidates | clip_ids | Parse structured result or a single JSON text block, reject missing/duplicate/excess IDs |
| Completion | audio-wait | Build ids/until=complete batches of at most twelve, further limited by schema |
| Single candidate info | audio-retrieve | Capability discovery only; completion and duration must be verified in host |
| Musical analysis | audio-analysis | Capability discovery only; do not equate provider metadata with independent measurement |
| WAV retrieval | audio-download | Build confirm=false probe; classify requires_credit as separate approval and processing as pending. No URL persistence or fetching |
| Local audio | WAV PCM16 | Independent duration, near-full-scale count, experimental pulse tempo estimate |

Observed changes: older clip_count was removed; a single creation call yielded two songs in the cited observation. Neither exact output count nor generation cost is guaranteed. Duration is a target; strict capping could truncate the music, so the initial proposal sets duration_strict=false if supported. A missing field stops the planner rather than silently altering the request. Idempotency keys are attempt-specific and deterministic; this program does not retry paid requests. No unsupported numeric BPM or seed argument is sent.

## 3. Offline quick start

From the repository root in Python 3.11+:

    python -m pip install -r requirements-dev.txt
    python -m unittest discover -s tests -v
    python suno_optimizer.py inspect fixtures/mcp_observed_subset.mock.json

Use the existing LYRIC-DESIGN-FRAMEWORK export_handoff.py to produce a fictional test handoff. For a mock planning exercise (all credit quantities below are fabricated examples):

    python suno_optimizer.py plan fixtures/mcp_observed_subset.mock.json handoff.json --style "Japanese electronic rock" --bpm 140 --duration 30 --attempt-id mock-001 --approved-credits 20 --estimated-upper 10 --remaining 30 --max-candidates 2

Output is a proposal, not a generation call or an approval. Keep it local because lyrics can be private. Tests create synthetic click WAV files in temporary directories. For an authorized local PCM16 WAV:

    python suno_optimizer.py evaluate local.wav --bpm 140 --tolerance 5 --min-sec 20 --max-sec 40

Tempo is UNKNOWN for automatic acceptance unless the operator confirms the estimate using --confirmed-tempo. Even PASS only concerns BPM and duration, not the entire SRS. The pulse estimator is a synthetic-fixture baseline, not validated for polyphonic music, half/double tempo, rubato or complex meter. Near-full-scale sample count is not a proof of clipping or distortion. MP3/float PCM input is outside the initial scope.

## 4. P1 real account procedure (operator-controlled)

1. Use a supported client, e.g. Claude Code: configure using the official command:
       claude mcp add --transport http suno https://api.suno.com/mcp
   In a Claude Code session run /mcp and personally authorize. Do not paste tokens into the repository.
2. Request current tool definitions. Where the client permits export, save every raw tools/list result page as an array in a private local JSON file. This CLI consumes the result objects, not a transcript or a guessed schema. If the client cannot provide them, remain in offline mode and document BLOCKED. No raw export is assumed to be supported by every host.
3. Run inspect on that local file. Confirm the endpoint and schema hash. Recheck before use and after any schema change. The CLI cannot authenticate the provenance of an imported JSON file, so operator verification is mandatory.
4. In the authorized host check account usage and current costs; use operator-confirmed conservative upper bounds in plan. The approval fingerprint binds the proposed arguments and supplied bounds, but is not an authorization credential or automatic budget enforcement.
5. Only if allowed by plan/terms and the author explicitly approves, submit the exact checked proposal manually through the host. Save actual response privately and record the cost. Do not use unrestricted autonomous tool execution.
6. Run wait-plan on the actual exported call result:
       python suno_optimizer.py wait-plan local-tools.json local-create-result.json --max-candidates 2
   Verify every candidate reaches complete/error with the authorized host. Do not assume streaming is complete. Missing or unfamiliar result structures stop the CLI. Do not re-send an ambiguous creation.
7. If permitted, request the download using the generated proposal:
       python suno_optimizer.py download-plan local-tools.json CLIP_ID
   confirm=false only; if a credit is needed, stop for separate explicit approval. Use authorized client download or manual export. Analyze the locally saved WAV and compare with human observations. Never commit signed URLs, credentials, private IDs, unpublished audio or lyric files.
8. Record live date, client/server/model where available, exact costs, all outcomes and actual audio hashes in a private DVR. Publicly report only rights-cleared/redacted summaries.

## 5. SRS coverage (partial)

| SRS test | Current code / proposed test | Scope |
|---|---|---|
| T02 | lyric SHA validation | LF normalization, version and identifiers; full upstream schema compatibility not yet tested |
| T03/T04 | plan and tools_snapshot | Deterministic proposal, schema fingerprint, fixture pagination; raw schema export / paid contract NOT_RUN |
| T06 | candidate_ids / wait_calls | Mock structured envelopes and batching; no live status polling |
| T07 | download_probe / decision | Probe only, operator handles download |
| T08 | wav_metrics | PCM16 synthetic pulse and duration tests; real music NOT_RUN |
| T11 | evaluate | Two metric subset; no overall SRS acceptance |
| T13 | plan_create | Per-proposal operator supplied bounds; no persistent multi-run ledger |
| T19 | unit test CI | Network-free test execution after dependency installation |
| T20 | schema_check | Reject references, unobserved fields, ambiguous result; full security audit pending |

Missing: complete requirements schema, persistent run ledger/state machine, actual authorized tool execution, real-time spend reservation, lyric ASR/phoneme alignment, feedback policy, A/B experiment and downstream handoff. All are still planned. No claims of measured superiority.

The previous overview figure remains a dated requirements-stage illustration; it is not a screenshot of running software.
