#!/usr/bin/env python3
"""Recompute the LongMemEval Oracle tallies from the judgement files in this folder."""
import json, math
from pathlib import Path

def load(name, key="correct"):
    return {row["question_id"]: (bool(row[key]), row["question_type"]) for row in map(json.loads, Path(name).read_text().splitlines()) if row}

runs = {
    "HivemindOS (Sonnet 4.5)": load("hive-judgements.jsonl"),
    "Sibyl-Memory plugin (Sonnet 4.5)": load("sibyl-plugin-sonnet45-regraded.jsonl"),
    "Sibyl-Memory (Sonnet 4.6)": load("sibyl-sonnet46-regraded.jsonl"),
    "Sibyl-Memory (Opus 4.6)": load("sibyl-opus46-regraded.jsonl"),
}
hive = runs["HivemindOS (Sonnet 4.5)"]
ex = [qid for qid, (_, qtype) in hive.items() if qtype != "single-session-preference"]

def mcnemar(b, c):
    n, k = b + c, min(b, c)
    return 1.0 if n == 0 else min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)

for name, run in runs.items():
    correct = sum(run[q][0] for q in ex)
    total = sum(ok for ok, _ in run.values())
    print(f"{name:34s} {correct}/{len(ex)} = {100 * correct / len(ex):.1f}% excluding preference; {total}/{len(run)} = {100 * total / len(run):.1f}% including")
for name, run in list(runs.items())[1:]:
    ours = sum(hive[q][0] and not run[q][0] for q in ex)
    theirs = sum(run[q][0] and not hive[q][0] for q in ex)
    print(f"  vs {name}: {ours} right only for HivemindOS, {theirs} only for Sibyl-Memory, exact McNemar p = {mcnemar(ours, theirs):.4f}")
