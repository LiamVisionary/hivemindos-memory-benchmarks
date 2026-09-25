#!/usr/bin/env python3
"""
Check that the memory context handed to the answering model contains nothing but that question's own chat history.

For every question in contexts.jsonl, every piece of conversation text in the context must appear word for word in the
chat history LongMemEval gives that question (longmemeval_oracle.json). Only the labels memory adds are allowed around
it: the recall scope line, each result's title and file path, and each session's date heading. Nothing from the answer
key, another question, or the grader can reach the model without failing this check.

Free to run, no API key:
  1. Download longmemeval_oracle.json from https://huggingface.co/datasets/xiaowu0162/longmemeval-cleaned
  2. python3 verify_contexts.py path/to/longmemeval_oracle.json
"""
import hashlib
import json
import re
import sys
from pathlib import Path

DATASET_SHA256 = "821a2034d219ab45846873dd14c14f12cfe7776e73527a483f9dac095d38620c"
HERE = Path(__file__).parent
STRUCTURAL = [
    re.compile(r"^Recall scope: "),
    re.compile(r"^From past conversations \(best-matching exchanges, oldest first\):$"),
    re.compile(r"^### Session \d+ · \d{4}/\d{2}/\d{2} \([A-Z][a-z]{2}\) \d{2}:\d{2}"),
    re.compile(r"^\d+\. .+ \([a-z-]+, score [\d.]+\)$"),
    re.compile(r"^Path: "),
]
MIN_FRAGMENT = 12


def normalise(text):
    # Markdown emphasis, heading and code marks are dropped on both sides; memory renders notes that wrote them.
    return re.sub(r"\s+", " ", re.sub(r"[*#`>]", "", text)).strip()


def main():
    dataset_path = Path(sys.argv[1] if len(sys.argv) > 1 else "longmemeval_oracle.json")
    raw = dataset_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != DATASET_SHA256:
        sys.exit(f"dataset sha256 {digest} is not the published file {DATASET_SHA256}")
    dataset = {q["question_id"]: q for q in json.loads(raw)}
    checked = fragments = 0
    failures = []
    for line in (HERE / "contexts.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if hashlib.sha256(row["context"].encode()).hexdigest() != row["context_sha256"]:
            failures.append((row["question_id"], "context does not match its own sha256"))
            continue
        question = dataset[row["question_id"]]
        history = normalise(" ".join(turn["content"] for session in question["haystack_sessions"] for turn in session))
        for text in row["context"].splitlines():
            text = text.strip()
            if not text or any(pattern.search(text) for pattern in STRUCTURAL):
                continue
            text = re.sub(r"^(User|Assistant|[A-Za-z][\w .'-]{0,40}): ", "", normalise(text))
            # Excerpts join turns with speaker labels and mark cuts with an ellipsis; check each piece between them.
            for piece in re.split(r"…|\.\.\.|\b(?:User|Assistant): ", text):
                piece = normalise(piece)
                if len(piece) < MIN_FRAGMENT:
                    continue
                fragments += 1
                if piece not in history:
                    failures.append((row["question_id"], piece[:120]))
        checked += 1
    print(f"{checked} contexts, {fragments} conversation fragments checked against each question's own history")
    if failures:
        print(f"{len(failures)} fragments NOT found in that question's history:")
        for question_id, piece in failures[:40]:
            print(f"  {question_id}: {piece}")
        sys.exit(1)
    print("every fragment appears word for word in that question's own chat history")


if __name__ == "__main__":
    main()
