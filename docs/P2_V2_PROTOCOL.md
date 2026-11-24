# P2 v2 paired-block policy pilot (pre-registered 2026-11-25 JST)

Goal: estimate the descriptive effect of a provider-feedback policy across three new synthetic lyric/tempo blocks. User authorized appropriate credit use; this run voluntarily limits to 90 song credits (nine standard calls, two songs each), no paid downloads initially. Standard v6 is 10 credits per call per official v6 FAQ and P1 observation. One call at a time, no Max Mode, no references, no replay; reconcile all candidates, model/controls and cost delta before proceeding. Stop on unresolved submission/cost, user interruption, or missing initial analysis. This is provider-only, not the production independent QA gate.

Each block starts with a shared initial call (I), style_influence 0.4, v6, variety=0, 35 s soft duration, no other controls. Both conceptual arms receive the same initial outcomes and have equal budget of 20 credits including a 10-credit allocation for I. Actual cost per block is 30 because I is shared. Regardless of initial pass count, generate exactly one follow-up per arm. A repeats 0.4; B uses 0.5 if either initial candidate fails the provider tempo/duration endpoint, otherwise repeats 0.4. If initial evidence is unknown, stop the block before follow-ups. This is a new candidate-level objective, not a retrospective amendment of v1. No selection or deletion of failed candidates.

| Block | BPM | Lyric (verse / chorus) | Order |
|---|---:|---|---|
| 01 | 175 | 夜空を越えて / 星を数える / 風を感じて / 明日へ走る | I, B, A |
| 02 | 95 | 静かな海に / 朝日がのぼる / 波の向こうへ / 心をひらく | I, A, B |
| 03 | 155 | 街の灯りを / ひとつ見つけた / 道をつないで / 未来へ進む | I, B, A |

Exact style template: "Japanese electronic rock, target tempo {BPM} BPM, steady four-on-the-floor, clear vocals, concise verse and chorus, natural ending". Lyrics formatted with [Verse] first two lines and [Chorus] last two lines, each line LF, final LF. Titles unique for reconciliation only. All calls duration=35, duration_strict=false, model=v6, controls.variety=0.

Primary endpoint: follow-up candidate count within target BPM ±5 and duration 25–45 s (0–2 per arm/block). Missing measurements count as nonpass. Compare paired block differences in counts, also total pass fraction and mean absolute BPM error (known values only, missing count separate). Shared initial not double counted in follow-up endpoint. Report trigger incidence and all outcomes including failures, actual costs and protocol deviations. Blocks not sufficient for statistical superiority; no inference treating candidates within calls as independent. No final lyric/tempo acceptance, independent WAV QA or downstream handoff claimed. If no intervention fires, policy mechanism not tested in this run. Stop after three blocks regardless of observed results.
