#!/usr/bin/env python3
"""Recompute every published number from the files in this folder. Free, no API key, no network."""
import json, math
from pathlib import Path

HERE = Path(__file__).parent
read = lambda path: [json.loads(line) for line in (HERE / path).read_text(encoding="utf-8").splitlines() if line]
contexts = {row["question_id"]: row["context_sha256"] for row in read("contexts.jsonl")}

def run(folder):
    hypotheses = {row["question_id"]: row for row in read(f"{folder}/hypotheses.jsonl")}
    for qid, row in hypotheses.items():
        assert row["context_sha256"] == contexts[qid], f"{folder} {qid}: answer was not given the published context"
    return {row["question_id"]: (row["correct"], row["question_type"]) for row in read(f"{folder}/judgements.jsonl")}

runs = {
    "HivemindOS, Claude Opus 4.6": run("opus-4.6"),
    "HivemindOS, Claude Sonnet 4.5": run("sonnet-4.5"),
}
for name, file in [("Sibyl-Memory, Claude Opus 4.6", "sibyl-opus46"), ("Sibyl-Memory plugin, Claude Sonnet 4.5", "sibyl-plugin-sonnet45"), ("Sibyl-Memory, Claude Sonnet 4.6", "sibyl-sonnet46")]:
    runs[name] = {row["question_id"]: (row["correct"], row["question_type"]) for row in read(f"sibyl-memory-regraded/{file}.jsonl")}

ids = sorted(runs["HivemindOS, Claude Opus 4.6"])
assert all(sorted(r) == ids for r in runs.values()) and len(ids) == 500, "every run covers the same 500 questions"
ex = [q for q in ids if runs["HivemindOS, Claude Opus 4.6"][q][1] != "single-session-preference"]
print("Every answer was given exactly the published context (sha256 checked).\n")
print(f"{'':40s} {'excluding preference':>22s} {'all 500':>16s}")
for name, r in runs.items():
    a = sum(r[q][0] for q in ex); b = sum(r[q][0] for q in ids)
    print(f"{name:40s} {a:>4d}/470 = {100*a/470:5.1f}%     {b:>4d}/500 = {100*b/500:5.1f}%")

def mcnemar(ours, theirs):
    n, k = ours + theirs, min(ours, theirs)
    return 1.0 if n == 0 else min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)

print("\nSame model, question by question (excluding preference):")
for hive, sibyl in [("HivemindOS, Claude Opus 4.6", "Sibyl-Memory, Claude Opus 4.6"), ("HivemindOS, Claude Sonnet 4.5", "Sibyl-Memory plugin, Claude Sonnet 4.5")]:
    ours = sum(runs[hive][q][0] and not runs[sibyl][q][0] for q in ex)
    theirs = sum(runs[sibyl][q][0] and not runs[hive][q][0] for q in ex)
    print(f"  {hive} vs {sibyl}: right only for HivemindOS {ours}, only for Sibyl-Memory {theirs}, exact McNemar p = {mcnemar(ours, theirs):.3f}")
