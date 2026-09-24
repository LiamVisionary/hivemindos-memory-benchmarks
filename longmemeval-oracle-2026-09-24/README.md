# HivemindOS Superbrain on LongMemEval Oracle — 2026-09-24

This measures Superbrain recall (`hive-brain answer`), not the NFT miner.

## Result

| System | Answer model | Correct, excluding preference (470) | Including preference (500) |
|---|---|---|---|
| **HivemindOS Superbrain** (hivemindos `27e1b10d`) | Claude Sonnet 4.5 | **447 (95.1%)** | **473 (94.6%)** |
| Sibyl-Memory plugin, published answers | Claude Sonnet 4.5 | 436 (92.8%) | 461 (92.2%) |
| Sibyl-Memory, published answers | Claude Sonnet 4.6 | 430 (91.5%) | 452 (90.4%) |
| Sibyl-Memory, published answers | Claude Opus 4.6 | 448 (95.3%) | 475 (95.0%) |

Every row is graded by the same judge: the official LongMemEval per-type judge prompts with `gpt-4o-2024-08-06`. Sibyl-Memory's answers are their own published hypothesis files from `Sibyl-Labs/memory-bench-kit` (`longmemeval/results/`). We re-graded them and did not re-run their system. Preference questions are left out of the headline, as in Sibyl-Memory's convention. Both figures are shown.

Paired against Sibyl-Memory on the same 470 questions (exact McNemar):
- **Plugin, Sonnet 4.5:** 21 right only for us, 10 only for them (p = 0.07).
- **Sonnet 4.6:** 27 against 10 (p = 0.008).
- **Opus 4.6:** 18 against 19 (p = 1.0).

## Not measured

HivemindOS was not run with Claude Opus 4.6 on the full 500, so there is no same-model comparison with Sibyl-Memory's Opus 4.6 row. A partial check answered 83 questions with Opus 4.6 on the same contexts: Sonnet 4.5's 23 misses and 60 of its correct answers. That is not a score and is not reported as one.

## Method

- **Dataset:** `longmemeval_oracle.json` from `xiaowu0162/longmemeval-cleaned`, sha256 `821a2034d219ab45846873dd14c14f12cfe7776e73527a483f9dac095d38620c`, all 500 questions.
- **Memory:** for each question, a fresh, empty vault. Each history session is written through the product's own conversation archive and indexed.
- **Recall:** the question is asked through the product's answer path, as `hive-brain answer` asks it: question budget, the typed-decision model ordering exchanges that do not fit, and the question date as "today".
- **Reading:** Claude Sonnet 4.5 via OpenRouter, temperature 0, 1,500 output tokens, with the official LongMemEval chain-of-thought reading prompt, unchanged.
- **Harness:** the HivemindOS LongMemEval harness (phases `retrieve` then `answer`, arm `product-answer-jev`). It lives in the HivemindOS source, which is not public.
- **Reuse:** 198 answers came from the development runs of the same code. They were reused only where the context was byte-identical, checked by sha256.

## Files

- `hive-hypotheses.jsonl`: one line per question (`question_id`, `question_type`, `question`, `gold`, `hypothesis`, `model`), in the format of Sibyl-Memory's scorer.
- `hive-judgements.jsonl`: the judge's verdict per question.
- `sibyl-plugin-sonnet45-regraded.jsonl`, `sibyl-sonnet46-regraded.jsonl`, `sibyl-opus46-regraded.jsonl`: the same judge's verdicts on Sibyl-Memory's published answers (`question_id`, `question_type`, `judge`, `correct`; their answer text stays in their repository).
- `tally.py`: recomputes every number above from these files (`python3 tally.py`).
- `score-sheet.txt`: the tallies above, by question type.

## Note on Sibyl-Memory's string scorer

`memory-bench-kit`'s `longmemeval-score.mjs` accepts any answer that contains the gold string. For example, a gold answer of "4" matches "May 14". On step-by-step answers it scores almost everything as correct, so none of the numbers above use it.
