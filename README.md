# SUNO-GENERATION-OPTIMIZER

[![Offline CI](https://github.com/Gacky-Lab/SUNO-GENERATION-OPTIMIZER/actions/workflows/phase0.yml/badge.svg?branch=main)](https://github.com/Gacky-Lab/SUNO-GENERATION-OPTIMIZER/actions/workflows/phase0.yml) · [Gacky-Lab research portfolio](https://github.com/Gacky-Lab/AI-MUSIC-VIDEO-STUDIO/blob/main/docs/profile/README.md)


A closed-loop music generation optimization framework using Suno MCP, automated quality evaluation, requirements verification, prompt optimization, and reproducible experiments. Developed by Gacky-Lab.

**生成AI音楽の閉ループ生成制御・要求適合性検証・条件最適化基盤**

- Maintainer: Gacky-Lab
- Status: Partial P2 implementation / repeated provider-feedback experiments (2026-11-25 JST)
- Official Suno MCP: https://api.suno.com/mcp — authenticated connector and paid standard generation verified; raw MCP schema export and autonomous execution not verified.
- 本プロジェクトは独立した研究開発であり、Suno公式製品・提携事業ではありません。

## System overview / システム構想

![生成AI音楽の閉ループ生成制御・要求適合性検証・条件最適化の構想図（要件定義段階、実機未検証）](images/overview-16x9.svg)

- [16:9 SVG原図](images/overview-16x9.svg)
- [HTML原本（保存してブラウザで表示）](docs/overview-16x9.html)
- PNG出力は [Render system overview PNG](https://github.com/Gacky-Lab/SUNO-GENERATION-OPTIMIZER/actions/workflows/render-overview.yml) で同一原図から生成。出力成功後は `images/overview-16x9.png` に保存されます。
- 図は要件定義の概要であり、実装・実機試験・性能実証の結果ではありません。正本は要件定義書です。

## Requirements / 要件定義

**[システム要件定義書 v0.1.0（SGO-SRS-001）](docs/requirements.md)**

公式MCPの公開機能を基準に、楽曲要求、生成・解析、独立検査、予算付き再生成、データ契約、DVP/DVR、研究比較計画を定義しています。ツール名・引数・権限・費用は認証後に確認します。

```mermaid
flowchart LR
  L[Lyric Design] --> R[Requirements]
  R --> G[Suno MCP]
  G --> Q[Independent QA]
  Q -->|Fail / within budget| R
  Q -->|Pass and human approval| V[AI Vocaloid Studio]
```

## Executable Phase-0 subset / オフライン実装

- [MCPインターフェース根拠・実行手順・検証範囲](docs/PHASE0_INTERFACE.md)
- [Python CLI](suno_optimizer.py): imported tools/list contract validation, generation proposal, candidate batching, download probe, independent PCM16 WAV QA.
- [Synthetic / mock tests](tests/test_phase0.py) / [CI status](https://github.com/Gacky-Lab/SUNO-GENERATION-OPTIMIZER/actions/workflows/phase0.yml)
- `python -m pip install -r requirements-dev.txt`
- `python -m unittest discover -s tests -v`
- `python suno_optimizer.py inspect fixtures/mcp_observed_subset.mock.json`

The mock fixture is not a live server capture. CLI never makes network calls or spends credits. The overview above describes the design, not the scope of the implemented subset.

## Authenticated Suno connector verification

**[Authenticated interface audit and redacted DVR](docs/AUTHENTICATED_INTERFACE_DVR.md)** — account usage, existing-song retrieval, analysis, alignment and completion wait succeeded. Generation and download credit balances unchanged. No private account values are published.

- [Provider evidence and bounded feedback helpers](live_evidence.py): redacted summaries, mandatory quality gate, one-factor revision proposal, descriptive A/B aggregation.
- See the P1 creation DVR below for the subsequent generation smoke test. Independent real-audio measurement completed in the follow-up; full acceptance and end-to-end quality improvement remain unverified.

## P1 generation attempt

- [Creation reconciliation DVR](docs/P1_CREATION_RECONCILIATION.md): one authorized standard generation reconciled to two completed private candidates, 10 song credits consumed. Host response decode failed; recovered without replay. Both WAV downloads authorized (2 download credits); manual private upload enabled independent WAV measurement on both candidates. Core offline CI: 23/23 on Python 3.11 and 3.13. Optional real-audio analyzer executed locally; mandatory tempo/lyric acceptance and controlled optimization comparison remain unverified.

## Independent WAV measurement

- [independent_qa.py](independent_qa.py) / [audio dependencies](requirements-audio.txt): spectral-onset beat estimation, tempo alternatives, decoded duration, loudness and true peak using librosa / FFmpeg. Actual two-song results in the P1 DVR. Local execution only, no private audio in Git. No automatic acceptance.

## P2 provider-feedback pilot

- [Pre-registered protocol](docs/P2_PILOT_PROTOCOL.md), [separate intervention protocol](docs/P2_INTERVENTION_PROTOCOL.md), [DVR](docs/P2_PILOT_DVR.md).
- Ten completed private candidates; 50 song credits, zero download credits. Fixed conditions: 7/8 provider endpoint passes. Separate one-factor intervention: 1/2; no proven efficacy. Independent audio acceptance remains UNKNOWN.
- Reproduce descriptive results: `python p2_pilot.py fixtures/p2_pilot_provider_results.json`.

## P2 repeated experiments (v2/v3)

- [V2 protocol](docs/P2_V2_PROTOCOL.md), [V3 protocol](docs/P2_V3_PROTOCOL.md), [complete DVR](docs/P2_REPLICATED_DVR.md).
- 26 additional private candidates / 130 song credits. V2 fixed conditions 13/18 provider endpoint passes, no adaptive trigger; V3 matched follow-up A 3/4, B 2/4. The tested control change has **no demonstrated advantage**. No independent acceptance or statistical efficacy claim.
- Reproduce: `python p2_replicated.py fixtures/p2_replicated_provider_results.json`.
- [Offline verification helpers](verification.py): transcript CER, fail-closed budget reservation and atomic checkpoint/reconciliation. No live network calls. Audio regression tests are in a separate workflow.

## Development roadmap

| Phase | Scope | Status |
|---|---|---|
| P0 | Offline CLI, schema import, proposal validation, basic WAV metrics | Partial implementation; see CI |
| P1 | Authorized Suno MCP generation and evidence collection | One generation reconciled; both WAVs independently measured; full acceptance pending |
| P2 | Budget-bounded feedback loop and baseline comparison | Repeated provider-only pilots and operator-directed interventions completed; superiority unproven; independent closed-loop efficacy NOT_RUN |
| P3 | MIDI control, editing difference, reproducibility research | Planned |

## Related projects

- [LYRIC-DESIGN-FRAMEWORK](https://github.com/Gacky-Lab/LYRIC-DESIGN-FRAMEWORK): lyric design and versioned Lyric Handoff.
- [AI-VOCALOID-STUDIO](https://github.com/Gacky-Lab/AI-VOCALOID-STUDIO): downstream vocal synthesis and DAW integration design.

## Safety and research boundaries

Default to offline tests. Live generation requires authorized access, explicit budget approval and confirmed tool capabilities. Do not commit credentials, signed URLs, unpublished music or private logs. Human approval is required before handing off an accepted track; no automatic release. Evaluation thresholds are provisional, not proven predictions of musical appeal or commercial success.

The requirements document is the current source of truth. No full operational optimizer, autonomous paid generation integration or measured quality improvement is claimed at this stage.
