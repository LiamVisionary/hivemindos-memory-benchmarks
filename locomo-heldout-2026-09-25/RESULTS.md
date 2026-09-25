# LoCoMo held-out test — results (2026-09-25)

Run exactly as pre-registered in `PREREGISTRATION.md` (commit `96b5f18` of this repository, pushed before any answer). 500 LoCoMo questions, Claude Opus 4.6 reading, `gpt-4o-2024-08-06` judging with Mem0's pinned LoCoMo prompts.

## Primary result

| | A: before (`7dc41be`) | B: after (`78e884d`) |
| --- | ---: | ---: |
| All 500 | 467 (93.4%) | **472 (94.4%)** |
| Multi-hop (92) | **86** | 84 |
| Temporal (104) | 97 | **99** |
| Open-domain (31) | 23 | **24** |
| Single-hop (273) | 261 | **265** |

Question by question, B answered 13 that A missed and A answered 8 that B missed (exact McNemar, p = 0.38).

**What it shows:** the memory changes made while working on LongMemEval did not hurt on a dataset they were never tuned on, and scored one point higher, but the difference is within chance. They are not shown to be overfit, and they are not shown to help on LoCoMo either.

**Cost of the difference:** B hands the reading model about twice as much text (median context 45,250 characters against 22,253), because it now sends whole histories and whole user turns where A cut to excerpts.

## Secondary analysis: failed for a setup reason

The pre-registered secondary run archived both speakers as the user. HivemindOS's conversation archive does not save a transcript with no assistant turn, so both versions stored nothing and every context is empty (52 characters: a recall-scope line). Both arms therefore answered without memory (A 32.6%, B 31.2%). This measures nothing about memory; it is published as run, and it was not redesigned or re-run afterwards.

## Check it

```bash
python3 tally.py
```

recomputes every number above from `runs/*/answers.jsonl` after checking that each answer was given the published context (sha256). `runs/<arm>/contexts.jsonl` holds exactly what memory handed the reading model; `answers.jsonl` holds the reading model's full output, the extracted answer, and the judge's reply. `benchmark-locomo-heldout.mjs` is the runner; `prompts/mem0-locomo-prompts.json` holds Mem0's prompts as sent.

## Notes

- One run per arm. Reader and judge variance at temperature 0 is a few questions either way (on LongMemEval Oracle, re-answering 475 unchanged contexts flipped 5).
- Mem0's judge is lenient by design (partial lists and close dates count), so absolute LoCoMo scores here are not comparable to scores graded differently.
- HivemindOS source is private; the commits are named for an auditor with access.
