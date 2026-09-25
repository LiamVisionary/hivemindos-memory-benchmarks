# LongMemEval_S: HivemindOS against Sibyl-Memory's published architecture — results (2026-09-25)

Run as pre-registered in `PREREGISTRATION.md` (commit `e069e8a` of this repository), with the deviations listed below. All 500 LongMemEval_S questions; Claude Opus 4.6 reads on both sides; every answer graded by LongMemEval's official per-type judge prompts with `gpt-4o-2024-08-06`.

## Result

| | HivemindOS | Sibyl-Memory (native architecture) |
| --- | ---: | ---: |
| Excluding preference (470) | **443 (94.3%)** | 433 (92.1%) |
| All 500 | **470 (94.0%)** | 457 (91.4%) |
| Updated facts (78) | **74** | 70 |
| Counting across chats (133) | 116 | **118** |
| Dates and time (133) | **127** | 121 |
| User facts (70) | **70** | 68 |
| What the assistant said (56) | 56 | 56 |
| Preferences (30) | **27** | 24 |
| Input tokens the reading model read, per question | **12,096** | 111,675 |

Question by question, excluding preference: HivemindOS answered 26 that Sibyl-Memory missed, Sibyl-Memory 16 that HivemindOS missed (exact McNemar, p = 0.16). All 500: 31 against 18 (p = 0.085).

**What it shows:** on the same questions with the same reading model and judge, HivemindOS scored higher while handing the model about a ninth of the text: memory returns ~12,100 tokens to read once, where Sibyl-Memory's architecture has Claude Code read the question's whole chronological journal (~111,700 tokens across its turns, cached reads included). **What it does not show:** a difference established beyond chance.

## Deviations from the pre-registration (all disclosed)

- **Two runners at once.** Two forked copies of the running agent session resumed Sibyl-Memory's run while the original was still answering, so 200 questions were answered twice. The kept answer for each question is the first valid one recorded in file order (a rule applied after the fact, before any duplicate was graded). `sibyl-native/hypotheses-raw-before-dedupe.jsonl` holds every record, duplicates and failures included; choosing the later duplicate instead is a one-line change for anyone who wants to check its effect.
- **Credit interruptions.** The Anthropic account ran out of credit three times. Every request refused for credit ("Credit balance is too low") was re-sent, as the pre-registration allows for infrastructure failures; none is counted.
- **Timer.** As pre-registered, Sibyl-Memory's per-question kill timer was 600 s instead of 120 s; no answer in the kept set timed out.
- HivemindOS's answers were produced before the pre-registration (their score was known), as the pre-registration states.

## Check it

```bash
python3 tally.py
```

recomputes every number above, checks that each HivemindOS answer was given its published context (sha256), and that both sides cover the same 500 questions. Files: `hivemindos/contexts.jsonl` (exactly what memory handed the reading model), `hivemindos/answers.jsonl` (answers, verdicts, token usage); `sibyl-native/hypotheses.jsonl` (Sibyl-Memory's runner output), `sibyl-native/judgements.jsonl`, `sibyl-native/claude-runs.jsonl` (Claude Code's own record of every run: turns, tokens, cost, answer), `claude-wrapper.sh`.

## Notes

- One run per side. At temperature 0 a few answers still move between runs (on LongMemEval Oracle, re-answering 475 unchanged contexts flipped 5).
- Sibyl-Memory's architecture runs through Claude Code, whose default settings may differ from a bare API call; it ran with an empty home directory so no local settings, hooks or instructions reached it.
- Sibyl-Memory's plugin product was not run: its benchmark integration is shared only with its beta testers. This compares Sibyl-Memory's published native architecture, the one behind its Opus 4.6 LongMemEval result.
- HivemindOS source is private; the memory code is hivemindos-core `ac0980b`.
