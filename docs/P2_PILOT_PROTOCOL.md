# P2 pilot protocol v1 (2026-11-25 JST)

Registered before new generation. Operator authorized appropriate credits; this pilot voluntarily caps song credits at 40 (four standard calls, two candidates each, 10 credits per call as observed in P1). No downloads, MIDI, stems, Max Mode or publishing. Sequential calls; reconcile balance and candidate count before next call; stop on unknown cost or response, unless independently reconciled by unique title, matching metadata and observed account delta.

Exploratory provider-feedback pilot, not full independent-QA closed-loop validation. Primary descriptive endpoint: proportion of candidates with provider BPM within 175 ± 5 and duration within 25–45 s, with missing values counted as not meeting endpoint. Secondary: absolute tempo error. Two calls per arm, one initial and one follow-up, equal fixed budgets; each call yields correlated candidates, not independent replications. No inferential significance claims.

Same synthetic lyrics, v6, 35 s soft duration, variety=0, initial style_influence=0.4, same style string for all attempts: "Japanese electronic rock, target tempo 175 BPM, fast steady four-on-the-floor, clear vocals, concise verse and chorus, natural ending". Title differs only to allow safe reconciliation. Lyrics:
[Verse]
遠い空へ
風を追いかける
[Chorus]
走り出そう
光の向こうへ

Order A1, B1, B2, A2. A2 repeats A1. B2 increases style_influence by 0.1 only if no B1 candidate meets both provider endpoints, all B1 data are known, and approved remaining cost is sufficient; otherwise B2 repeats B1 as a fixed-budget comparator (no adaptive step occurred). All candidate outcomes reported, no selective omission. This is an explicitly provider-only experimental policy, not the independent production gate in live_evidence.py. No final acceptance or downstream handoff. If a real corrective step occurs, it is only a one-factor hypothesis. No proof of superiority from one run per arm.

All raw responses, clip IDs, links, private account details stay out of Git. Record only aggregate or synthetic candidate measurements, actual credit delta and limits. Independent WAV review would require separate file transfer; not included in this pilot.
