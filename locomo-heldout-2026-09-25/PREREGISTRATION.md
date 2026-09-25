# LoCoMo held-out test — pre-registration (2026-09-25)

Written and pushed before any LoCoMo question was answered by any version below. Nothing in this plan changes after this commit; the results, whatever they are, go in this folder.

## Question

HivemindOS's LongMemEval Oracle result (91.1% -> 95.1% with Claude Sonnet 4.5, then 96.6% with Claude Opus 4.6) came from memory changes found by studying misses on those same 500 questions, and LongMemEval_S shares those questions. Do the changes also help on data they were never tuned on?

LoCoMo was not used to develop any of them. This is a comparison of two HivemindOS versions with each other, not with any other memory system.

## Versions

| Arm | hivemindos-core commit | What it is |
| --- | --- | --- |
| A (before) | `7dc41be` | The memory code of the first full Oracle run (91.1% with Sonnet 4.5). Every change credited for 91.1% -> 95.1% and 96.6% came after it. |
| B (after) | `78e884d` | Current memory code (identical under `src/` to `ac0980b`): whole histories to 60,000 characters, date recall, session ages, no duplicate excerpts, nearby conversations fill a question's room, long histories keep every user turn whole, user turns first then the best replies. |

The source is private; the commits are named so an auditor with access can check them. Arm A runs this folder's `benchmark-locomo-heldout.mjs` (sha256 `4bbc822e1606418f6dc7d6b2398c9a70ce535bd2859e354e2df1c3a64c8eef7b`, identical to the file at `78e884d`) copied into a checkout of `7dc41be`; each arm formats memory's answer with its own commit's `hive-brain answer` formatting.

## Data and sample

- Dataset: `locomo10.json` from `snap-research/locomo@3eb6f2c585f5e1699204e3c3bdf7adc5c28cb376`, sha256 `79fa87e90f04081343b8c8debecb80a9a6842b76a7aa537dc9fdf651ea698ff4`.
- Scored categories 1-4 (multi-hop, temporal, open-domain, single-hop): 1,540 questions. Category 5 (adversarial) is excluded, as in Mem0's LoCoMo method.
- Sample: 500 questions, per category the ones with the lowest sha256("hivemindos-locomo-heldout-2026-09-25:<conversation index>:<question index>"), in proportion to each category's size: 92 multi-hop, 104 temporal, 31 open-domain, 273 single-hop. `sample.json`, sha256 `66165e52c2d4022ce5e06394a7926f2806f6bbd95b018a910109520413d7c585`.

## Memory

- Each conversation is written into a fresh, empty vault through the product's own conversation archive and full-vault index; every sampled question from that conversation is then put to memory the way `hive-brain answer` does it (question budget, limit 5). "Today" is the conversation's last session date.
- Speakers (primary): `speaker_a` is archived as the user and `speaker_b` as the other party, the mapping the July 2026 LoCoMo runs used. Image captions are kept as text.
- Both arms: no model ordering of exchanges (no Jev), no embeddings (lexical recall only), no conversation ledgers.

## Reading and grading (Mem0's pinned LoCoMo method)

- Prompts: `mem0ai/memory-benchmarks@4b61c5d31b9c668a12b4f5e78064248a02c82d2b`, `benchmarks/locomo/prompts.py` (sha256 `8ebac1ef60e9ab5caf99079fdaac038b85472e81491ed35e2d2655f3927c76c2`, Apache-2.0), rendered unchanged to `prompts/mem0-locomo-prompts.json` (sha256 `2d2e46015d944e86f10c2a6d6651334d06e493f1d51f2537c359ecfe2d0edcb6`).
- Reader: `claude-opus-4-6` through Anthropic's Message Batches API, temperature 0, max 1,500 output tokens, no extended thinking. Mem0's answer prompt with memory's answer as the memories, the last session's date string as the reference date, and the text after the last "ANSWER:" as the answer.
- Judge: `gpt-4o-2024-08-06` on OpenAI's API, temperature 0, JSON output, Mem0's judge system prompt and judge prompt without evidence (Mem0's default). An open-domain gold answer is judged on its part before ";" (Mem0). CORRECT counts as right.

## Analysis

- Primary: accuracy of B against A on the 500 questions, exact two-sided McNemar test on the questions only one arm got right. Reported per category as well.
- Secondary, run and reported in full: the same two arms with both speakers archived as the user (`--speakers both-user`), because arm B keeps user turns whole and shortens the other party's, and in LoCoMo both parties are people.
- LoCoMo's answer key has documented errors; no question is removed, and both arms face the same key.

## Commitments

- No code, prompt, sample or setting changes after this commit. A request that fails for a technical reason (API error, timeout) is re-sent; nothing is re-run because of its result.
- Every context (with its sha256), answer and verdict is published here, whatever the outcome.
