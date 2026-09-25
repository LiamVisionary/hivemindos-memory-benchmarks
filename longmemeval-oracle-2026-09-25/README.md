# HivemindOS Superbrain on LongMemEval Oracle — September 25, 2026

This measures Superbrain recall (`hive-brain answer`), not the HivemindOS NFT miner.

## Result

LongMemEval Oracle, all 500 questions. Every answer below, ours and Sibyl-Memory's own published ones, is graded by LongMemEval's official per-type judge prompts with `gpt-4o-2024-08-06`.

| System | Model that reads the memory | Excluding preference (470) | All 500 |
| --- | --- | ---: | ---: |
| **HivemindOS Superbrain** | Claude Opus 4.6 | **454 (96.6%)** | **483 (96.6%)** |
| Sibyl-Memory (published answers) | Claude Opus 4.6 | 448 (95.3%) | 475 (95.0%) |
| **HivemindOS Superbrain** | Claude Sonnet 4.5 | **447 (95.1%)** | **473 (94.6%)** |
| Sibyl-Memory plugin (published answers) | Claude Sonnet 4.5 | 436 (92.8%) | 461 (92.2%) |
| Sibyl-Memory (published answers) | Claude Sonnet 4.6 | 430 (91.5%) | 452 (90.4%) |

Question by question, on the same 470 questions:
- **Opus 4.6 against Opus 4.6:** HivemindOS answered 16 that Sibyl-Memory missed, and Sibyl-Memory 10 that HivemindOS missed (exact McNemar test, p = 0.33).
- **Sonnet 4.5 against Sonnet 4.5:** 21 against 10 (p = 0.07).

**What these numbers support:** with the same reading model and the same judge, HivemindOS scored higher than Sibyl-Memory's published runs.

**What they do not support:** a difference established beyond chance. Six questions out of 470 is within what a second run of either system could move.

Preference questions are excluded from the headline because Sibyl-Memory excludes them. Both figures are shown.

## Check it yourself

**Free, no API key, about a minute.** Download `longmemeval_oracle.json` from [xiaowu0162/longmemeval-cleaned](https://huggingface.co/datasets/xiaowu0162/longmemeval-cleaned) (sha256 `821a2034d219ab45846873dd14c14f12cfe7776e73527a483f9dac095d38620c`), then:

```bash
python3 verify_contexts.py path/to/longmemeval_oracle.json   # nothing but each question's own history reached the model
python3 tally.py                                             # every number above, recomputed from the files
```

- `contexts.jsonl` is exactly what HivemindOS memory handed the reading model for each question.
- `verify_contexts.py` checks every piece of conversation text in it against that question's own chat history in the public dataset: 81,369 pieces across 500 questions, all found word for word. Memory adds only labels around them: the recall scope line, result titles and paths, and dated session headings. Text from the answer key, another question, or the grader would fail the check. We confirmed it does by planting an answer in one context.
- Every answer records the sha256 of the context it was given. `tally.py` refuses an answer whose context is not the published one.

**On your own key, at your cost.**
- `regrade.py` grades any answer file again with the official judge. That covers ours, and Sibyl-Memory's from [their repository](https://github.com/Sibyl-Labs/memory-bench-kit/tree/main/longmemeval/results). About $1 for 500.
- `reread.py` has Claude read our published contexts again, with no HivemindOS code, so you can re-run the reading half of the benchmark from our exact inputs. About $0.04 a question for Opus 4.6; `--limit 50` samples it. `--dry-run` prints each prompt's sha256 for free.
- Expect small differences: the reading model and the judge are not perfectly repeatable even at temperature 0.

## How it was run

- **Memory.** For each question, a fresh, empty vault. Each of the question's conversations is written through the product's own conversation archive and indexed, then the question is asked through the product's answer path: the same path `hive-brain answer` uses.
  - The question's own date is "today".
  - Conversations that fit are handed over whole (up to 60,000 characters).
  - A decision model orders the exchanges when they do not fit.
  - HivemindOS code: `hivemindos-core` commit `27e1b10d`.
- **Reading.** LongMemEval's official chain-of-thought reading prompt, unchanged (`prompts/reader.txt`); temperature 0; 1,500 output tokens; no extended thinking.
  - Opus 4.6 (`claude-opus-4-6`) ran through Anthropic's Message Batches API, all 500 in one run on September 25, 2026.
  - Sonnet 4.5 (`anthropic/claude-sonnet-4.5`) ran through OpenRouter.
  - 198 of the Sonnet answers came from development runs of the same code on byte-identical contexts; their context fingerprints are checked like every other.
- **Grading.** `prompts/judge.mjs`, LongMemEval's per-type prompts as sent, to `gpt-4o-2024-08-06` through OpenRouter, for all 1,000 reported answers and for Sibyl-Memory's 1,500.
- **Sibyl-Memory.** We did not run Sibyl-Memory. We graded its published answer files (`sibyl-memory-regraded/`). Its own reported 95.6% (Opus) and 95.1% (plugin) come from its string-matching scorer; under the official judge they grade 95.3% and 92.8%.

## What you should know

- **Improvements were developed on this test set.** The changes that moved HivemindOS from 91.1% (Sonnet 4.5, first full run) to 95.1% were found by studying its misses on these 500 questions. There is no separate held-out set.
  - The changes are general product behaviour, not per-question rules:
    - finding conversations by the dates a question names;
    - labelling each session with its age;
    - handing over whole conversations when they fit;
    - not repeating an excerpt of a conversation above its full text.
  - They shipped in the product for every user.
- **Every full run we did on this set, not just the best.** Excluding preference, 470 questions:

| Run | Score |
| --- | ---: |
| Sonnet 4.5, first product version | 428 (91.1%) |
| Sonnet 4.5, reported | 447 (95.1%) |
| Sonnet 4.5 with conversation ledgers | 444 (94.5%) |
| Opus 4.6, reported | 454 (96.6%) |
| Opus 4.6 with conversation ledgers | 451 (96.0%) |

  Conversation ledgers are an optional feature that did not help here. The reported rows are the product as it ships, with ledgers off by default.
- **One run per configuration.** Model and judge variance between runs is a few questions either way.
- **What cannot be checked without our source.** That HivemindOS's own code produced these contexts. The HivemindOS source is not public. Everything downstream of the contexts can be reproduced from this folder.

## Files

| File | What it is |
| --- | --- |
| `contexts.jsonl` | For each question: `question_id`, `question_type`, `context` (what memory returned), `context_sha256` |
| `opus-4.6/hypotheses.jsonl`, `sonnet-4.5/hypotheses.jsonl` | Every answer, in Sibyl-Memory's scorer format, plus the model, the host and the `context_sha256` it was given |
| `opus-4.6/judgements.jsonl`, `sonnet-4.5/judgements.jsonl` | The judge's reply and verdict for every answer |
| `sibyl-memory-regraded/*.jsonl` | The same judge's verdicts on Sibyl-Memory's three published runs (their answer text stays in their repository) |
| `prompts/reader.txt`, `prompts/judge.mjs` | The reading and grading prompts, as sent |
| `verify_contexts.py`, `tally.py` | The free checks |
| `regrade.py`, `reread.py` | Re-grading and re-reading on your own key |
