# P1 creation attempt: safe reconciliation (2026-11-25 JST)

Status: SUBMISSION_UNKNOWN; no replay authorized.

## Preconditions

- Operator explicitly authorized up to 20 song-generation credits for validation.
- Standard v6 text-only generation, two songs per request: 10 credits according to the [official v6 FAQ](https://help.suno.com/en/articles/13924481) and [MCP FAQ](https://suno.com/mcp).
- Authenticated account usage confirmed model v6 and advanced-control grant. No Max Mode, media references, download confirmations, MIDI or stems requested.
- One creation invocation only, with a stable idempotency key, synthetic Japanese lyric, 140 BPM style instruction, 30-second soft duration, style_influence=0.8, variety=0. Exact identifiers, account balances and raw responses remain private.

## DVR

| Check | Result |
|---|---|
| Approved budget and official standard price | PASS |
| Authorized model / advanced-control preflight | PASS |
| Creation invocation | SENT; acceptance not established |
| Decode host creation response | FAIL — JSON decoder reported additional non-whitespace content after the first JSON value; the original response was not retained by the invoking script |
| Immediate balance comparison | No change observed |
| Finished library lookup by unique test title | No matching finished song observed on initial reads |
| Actual generation charge, candidate IDs, generation completion | UNKNOWN |
| Independent WAV and lyric QA | NOT_RUN |
| Paid replay / second generation | NOT_RUN |

The failed parser does not establish a server-side failure, acceptance, or absence of a charge. An empty finished-song search cannot exclude a pending creation. A fixed expected cost is not a charge receipt. No automatic retry or new generation while the attempt is unresolved. A later read may reconcile the attempt using the unique test title, timestamps, candidate IDs and account ledger; require two matching candidates or stop for manual review. Do not publish any song identifiers or private URLs.

## Required engineering change

Capture the response locally before parsing, with controlled retention and no publication of raw private data. Distinguish host response framing from raw MCP response framing. A synthetic regression test verifies that a JSON value followed by arbitrary text is rejected; this is deliberately not a replay of the actual response. Do not guess the undocumented suffix format or strip it to claim success. If the host provides separate structured response and presentation fields, validate the documented structured field. An authenticated read-only audit remains valid; this attempt does not establish successful paid creation or optimization performance.

The previous 22-case offline CI was successful on Python 3.11 and 3.13. The added regression is separately verified by CI. No claim of full P1 completion.
