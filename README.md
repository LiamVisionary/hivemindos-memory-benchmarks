# HivemindOS memory benchmarks

Published receipts for [HivemindOS](https://hivemindos.app) Superbrain memory benchmarks: every model answer, every judge verdict, the method, and a script that recomputes the score from the files.

| Folder | Benchmark | Result |
|---|---|---|
| [`longmemeval-s-sibyl-native-2026-09-25`](longmemeval-s-sibyl-native-2026-09-25/) | LongMemEval_S, all 500 questions, Claude Opus 4.6 on both sides, against Sibyl-Memory's own published architecture run by us with its public runner (pre-registered) | 94.3% (443/470) vs Sibyl-Memory 92.1% (433/470), p = 0.16, reading about a ninth of the text |
| [`locomo-heldout-2026-09-25`](locomo-heldout-2026-09-25/) | LoCoMo, 500 sampled questions, pre-registered held-out test of HivemindOS's own LongMemEval-era memory changes (before vs after), Mem0's pinned prompts | 93.4% -> 94.4%, p = 0.38: no overfitting shown, no gain shown |
| [`longmemeval-oracle-2026-09-25`](longmemeval-oracle-2026-09-25/) | LongMemEval Oracle, all 500 questions, Claude Opus 4.6 and Claude Sonnet 4.5, official gpt-4o judge, against Sibyl-Memory's published answers graded the same way, with the exact memory contexts and free checks | Opus 4.6: 96.6% (454/470) vs Sibyl-Memory 95.3%. Sonnet 4.5: 95.1% (447/470) vs 92.8% |
| [`longmemeval-oracle-2026-09-24`](longmemeval-oracle-2026-09-24/) | LongMemEval Oracle, all 500 questions, Claude Sonnet 4.5, official gpt-4o judge | 95.1% excluding preference (447/470), 94.6% including (473/500) | (superseded by the folder above, which holds the same Sonnet answers plus their contexts)

Results are measured on HivemindOS Superbrain recall, not on the HivemindOS NFT miner.
