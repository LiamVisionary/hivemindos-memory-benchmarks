#!/usr/bin/env python3
"""Recompute RESULTS.md from the published answers: accuracy, the paired McNemar test, per type, and tokens read."""
import hashlib, json, math, sys
from pathlib import Path

HERE = Path(__file__).parent
rows = lambda path: [json.loads(line) for line in (HERE / path).read_text().splitlines() if line.strip()]

contexts = {r["question_id"]: r for r in rows("hivemindos/contexts.jsonl")}
for r in contexts.values():
    if hashlib.sha256(r["context"].encode()).hexdigest() != r["context_sha256"]:
        sys.exit(f"{r['question_id']}: context does not match its sha256")
hive = {r["question_id"]: r for r in rows("hivemindos/answers.jsonl")}
for q, r in hive.items():
    if contexts[q]["context_sha256"][:16] != r["context_hash16"]:
        sys.exit(f"{q}: HivemindOS answer was not given the published context")
sibyl = {r["question_id"]: r for r in rows("sibyl-native/judgements.jsonl")}
hypotheses = {r["question_id"] for r in rows("sibyl-native/hypotheses.jsonl")}
assert set(sibyl) == hypotheses == set(hive), "both sides must cover the same 500 questions"


def mcnemar(a, b):
    n = a + b
    return 1.0 if n == 0 else min(1.0, 2 * sum(math.comb(n, k) for k in range(min(a, b) + 1)) / 2 ** n)


ids = sorted(hive)
for label, subset in [("all 500", ids), ("excluding preference", [q for q in ids if hive[q]["question_type"] != "single-session-preference"])]:
    h = sum(hive[q]["correct"] for q in subset); s = sum(sibyl[q]["correct"] for q in subset)
    only_h = sum(hive[q]["correct"] and not sibyl[q]["correct"] for q in subset)
    only_s = sum(sibyl[q]["correct"] and not hive[q]["correct"] for q in subset)
    print(f"{label:22s} HivemindOS {h}/{len(subset)} ({100*h/len(subset):.1f}%)  Sibyl-Memory native {s}/{len(subset)} ({100*s/len(subset):.1f}%)  only HivemindOS {only_h}, only Sibyl-Memory {only_s}, p = {mcnemar(only_h, only_s):.3f}")
for kind in sorted({r["question_type"] for r in hive.values()}):
    subset = [q for q in ids if hive[q]["question_type"] == kind]
    print(f"  {kind:26s} HivemindOS {sum(hive[q]['correct'] for q in subset)}/{len(subset)}  Sibyl-Memory {sum(sibyl[q]['correct'] for q in subset)}/{len(subset)}")
ours = [r["usage"]["input_tokens"] for r in hive.values() if r.get("usage")]
runs = [r for r in rows("sibyl-native/claude-runs.jsonl") if not r["is_error"] and "Credit balance" not in (r.get("result") or "")]
theirs = [sum(r["usage"].get(k, 0) for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")) for r in runs]
print(f"\ninput tokens a question: HivemindOS {sum(ours)/len(ours):,.0f} (one read)  Sibyl-Memory native {sum(theirs)/len(theirs):,.0f} (all turns, cached included; {len(runs)} successful Claude Code runs)")
