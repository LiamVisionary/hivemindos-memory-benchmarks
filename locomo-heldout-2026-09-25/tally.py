#!/usr/bin/env python3
"""Recompute every number in RESULTS.md from runs/*/answers.jsonl, after checking each answer was given its published context."""
import hashlib, json, math, sys
from pathlib import Path

HERE = Path(__file__).parent
NAMES = {1: "multi-hop", 2: "temporal", 3: "open-domain", 4: "single-hop"}


def load(run):
    contexts = {}
    for line in (HERE / "runs" / run / "contexts.jsonl").read_text().splitlines():
        row = json.loads(line)
        if hashlib.sha256(row["context"].encode()).hexdigest() != row["contextSha256"]:
            sys.exit(f"{run} {row['questionId']}: context does not match its sha256")
        contexts[row["questionId"]] = row["contextSha256"]
    answers = {}
    for line in (HERE / "runs" / run / "answers.jsonl").read_text().splitlines():
        row = json.loads(line)
        if contexts.get(row["questionId"]) != row["contextSha256"]:
            sys.exit(f"{run} {row['questionId']}: answer was not given the published context")
        answers[row["questionId"]] = row
    return answers


def mcnemar(a, b):
    n = a + b
    return 1.0 if n == 0 else min(1.0, 2 * sum(math.comb(n, k) for k in range(min(a, b) + 1)) / 2 ** n)


for mapping in ["user-assistant", "both-user"]:
    first, second = load(f"A-7dc41be-{mapping}"), load(f"B-78e884d-{mapping}")
    ids = sorted(set(first) & set(second))
    print(f"\nspeakers {mapping}: {len(ids)} paired questions")
    for label, subset in [("all", ids)] + [(NAMES[c], [i for i in ids if first[i]["category"] == c]) for c in NAMES]:
        a = sum(first[i]["correct"] for i in subset); b = sum(second[i]["correct"] for i in subset)
        only_a = sum(first[i]["correct"] and not second[i]["correct"] for i in subset)
        only_b = sum(second[i]["correct"] and not first[i]["correct"] for i in subset)
        print(f"  {label:12s} A {a}/{len(subset)} ({100*a/len(subset):.1f}%)  B {b}/{len(subset)} ({100*b/len(subset):.1f}%)  only A {only_a}, only B {only_b}, p = {mcnemar(only_a, only_b):.3f}")
