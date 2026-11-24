# Authenticated Suno interface audit and DVR (2026-11-25 JST)

Scope: authenticated ChatGPT Suno connector, existing owned song, read-only. No new generation, paid MIDI/stem processing, downloads, edits, publishing or account changes. No user IDs, song IDs/titles, lyrics, URLs, credit balances or musical measurements from the account are included here. The report is an author/operator observation, not a public raw server trace. The connector exposed 59 tools; the underlying raw MCP tools/list schema was not exported.

## Contract changes versus earlier third-party observation

| Interface | Confirmed from authenticated connector declaration | Implementation |
|---|---|---|
| account-usage | allowed_models, features, suno_account | actual read succeeded; model grants / advanced-control gate |
| audio-create | custom lyrics <=5000, style <=1000, model, duration 15–360, duration_strict, duration_guidance, idempotency_key 1–255 bytes | subset proposal only; no seed or numeric BPM field assumed |
| controls | style_influence / weirdness 0–1, variety integer 0–4; audio_influence only with voice_id | opt-in custom mode subset, omit defaults; validate grants |
| audio-create result | two songs per suno.com MCP call, clip_ids | declared only; paid generation NOT_RUN |
| audio-wait | ids max 12; until playable/complete; clips array in input order | changed previous conservative max 4 to 12, use complete for QA |
| audio-retrieve | status; metadata.duration, model, controls, lyrics for owned clips | actual read succeeded |
| audio-analysis | status processing/complete/unavailable, bpm, duration_s, beats, sections, key, time_signature, terms, labels | actual read succeeded after processing; partial data possible even on complete |
| audio-lyrics-alignment | words with word/start_s/end_s/success/p_align; complete/processing/unavailable | actual read succeeded; alignment not proof of lyric accuracy |
| audio-download | omit confirm first; requires_credit -> separate consent; processing -> same tool again | proposal only; NOT_RUN |
| audio-midi | Premier + grants; 10 song credits unless existing transcription or eligible stem | declared only; NOT_RUN |
| MIDI input | midi_upload_id, simple mode, v6-wild, upload/check before generation | declared only; NOT_RUN |
| audio-settings | visibility public/private, can_remix | excluded from automation; NOT_RUN |

For authenticated host results, the observed wrapper was a JSON string in a text property. It is distinct from standard MCP structuredContent / content text blocks. The adapter accepts the narrow observed envelope and rejects ambiguous/error responses.

## DVR: read-only integration observation

| Test | Expected | Observed | Status |
|---|---|---|---|
| L01 account usage | authenticated response, feature/model list | returned | PASS |
| L02 library list | items array, existing owned song | returned | PASS |
| L03 retrieve | complete status, metadata.duration numeric | returned | PASS |
| L04 analysis | processing or terminal; final numeric BPM/duration, structured arrays | processing then complete; numeric values and beat/section/tag arrays | PASS |
| L05 alignment | complete words array and matching audio_id | returned word objects with success and timing | PASS |
| L06 wait | until complete; matching clips array | complete; one existing clip | PASS |
| L07 cross-link | retrieve id = analysis/alignment audio_id | matched | PASS |
| L08 read-only cost | generation and download balances unchanged from initial recorded reading | unchanged | PASS |
| T04 raw tools/list export | raw paginated schema and hash | host tool declarations only | PARTIAL |
| T05/T06 paid generation and cost reconciliation | approved new generation with both candidate IDs | no approved budget; not sent | NOT_RUN |
| T08/T09 independent WAV vs provider | rights-cleared local WAV and independent metrics | no WAV transferred; synthetic tests separate | NOT_RUN |
| T10 lyric accuracy | independent ASR + human labels | alignment only | NOT_RUN |
| T12/T17 closed loop / A-B | approved equal-budget real experiments | offline policy and descriptive aggregation only | NOT_RUN |

No performance improvement is demonstrated by these reads. No claim of world-first status. Tool declarations may change; reduced mock fixture is independently reconstructed, not a raw schema capture. Operator must verify current account grants and actual costs before generation.

## Added local research helpers

- suno_optimizer.py: optional model and controls bound to imported account grants, deterministic proposal, current wait limit, connector envelope support.
- live_evidence.py: redacted provider-only evidence summary, candidate terminal-state validation, mandatory requirement gate, one-factor style-influence revision proposal and equal-budget run comparison.
- tests/test_live_evidence.py: synthetic fixtures for error paths, redaction, gate, budget and comparison.
- Provider tags and alignment cannot substitute for independent audio QA. A PASS requires independent/human source and explicit human approval for handoff; this helper trusts caller-supplied evidence classifications and is not a cryptographic proof system.
- The proposed style-influence step is a hypothesis, not a proven correction for tempo. It requires a new attempt ID, budget and schema validation, and human approval. No automatic paid calls or persistent job ledger exist yet.

## Run

    python -m pip install -r requirements-dev.txt
    python -m unittest discover -s tests -v

Use only private local files for raw responses:
    
    python live_evidence.py evidence local/retrieve.json local/analysis.json local/alignment.json
    python live_evidence.py compare local/runs.json

Results from the evidence CLI are local analysis outputs, not suitable for automatic release. The public DVR above is deliberately limited to structural outcomes. The current connector does not expose an automatic mechanism for exporting raw response files to the local CLI; these paths are operator-managed.

Next: explicit credit ceiling, one custom-mode generation, complete candidate/cost reconciliation, authorized WAV retrieval and independent inspection; then an approved A/B pilot. Do not infer the exact generation price from subscription limits. No unapproved download or MIDI credits.
