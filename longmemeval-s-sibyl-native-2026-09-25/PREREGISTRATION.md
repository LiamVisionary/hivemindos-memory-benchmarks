# LongMemEval_S: Sibyl-Memory's own published architecture against HivemindOS — pre-registration (2026-09-25)

Written and pushed before Sibyl-Memory's architecture answered any question in this run (a 3-question pilot on questions of the same set measured cost and timing only; its answers are not used).

## Why this comparison

Sibyl-Memory's published LongMemEval results are on Oracle, where each question comes with only the conversations that hold its answer. Its Opus 4.6 result comes from its native architecture: Claude Code reads the question's whole chronological chat journal with Sibyl's CLAUDE.md instructions. Its plugin result depends on an integration setup Sibyl-Memory shares only with beta testers, so it cannot be reproduced faithfully and is not run here. The native architecture's runner is public: `Sibyl-Labs/memory-bench-kit@9d2d381`, `longmemeval/runner/longmemeval-ingest.mjs` (sha256 `aae00e758930df17591239015f382883f12d65b69318b1b07020ca1939fbd8e0`) and `longmemeval-run.mjs` (sha256 `613c63dcac8502910db3a6dfb33fbaf03a9c4288991c5903400debe54fc78dca`).

LongMemEval_S asks the same 500 questions with each question's evidence among ~50 conversations (~490,000 characters), which is the setting a memory system is for.

## What runs

- **Sibyl-Memory (native architecture):** both runner files unmodified except one number: the per-question kill timer in `longmemeval-run.mjs` goes from 120 s to 600 s, because S journals are about ten times the Oracle journals the 120 s was set for (in the pilot, 1 of 3 questions was killed at 120 s with an empty answer). Claude Code 2.1.280, `claude-opus-4-6` (the model of Sibyl-Memory's published Opus answers). `claude-wrapper.sh` stands in for `claude` on PATH: it adds `--model claude-opus-4-6 --output-format json`, runs Claude Code with an empty HOME so no user settings, hooks or instruction files reach it, logs each run's cost and turns, and prints the answer text for the runner exactly as plain output would. All 500 S questions, concurrency 4.
- **HivemindOS:** the answers already produced on 2026-09-25 by hivemindos-core `ac0980b` (memory code identical to `78e884d`): `hive-brain answer`'s path with no Jev ordering and no embeddings, Claude Opus 4.6 through Anthropic's Message Batches API with LongMemEval's official reading prompt, temperature 0. That run's result is already known to us (470/500, 94.0%); it is not re-run.
- **Grading, both sides:** LongMemEval's official per-type judge prompts with `gpt-4o-2024-08-06` on OpenAI's API, the same judge every earlier result in this repository used.

## Analysis

- Primary: accuracy excluding the 30 preference questions (Sibyl-Memory's headline convention), paired over the 470 questions, exact two-sided McNemar test; also all 500 and per type.
- An answer Sibyl-Memory's runner records as an error or empty counts as wrong; the number of such answers is reported. A question that fails for an API or infrastructure reason is re-run.

## Commitments

- No change to either runner, prompt or judge after this commit. Everything — Sibyl-Memory's answers, costs, turns and verdicts, and ours — is published here whatever the outcome.
