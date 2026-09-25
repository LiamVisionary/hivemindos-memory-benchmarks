#!/usr/bin/env python3
"""
Have Claude read the published memory contexts again, on your own Anthropic key, then grade the answers with regrade.py.
This re-runs the reading half of the benchmark from our exact inputs, with no HivemindOS code.

  ANTHROPIC_API_KEY=... python3 reread.py claude-opus-4-6 path/to/longmemeval_oracle.json --limit 50 > mine.jsonl
  OPENAI_API_KEY=... python3 regrade.py mine.jsonl path/to/longmemeval_oracle.json

--dry-run prints each prompt's sha256 instead of calling the model (free), for checking the prompts are the ones we sent.
Opus 4.6 costs about $0.04 a question at standard prices. Answers vary a little from run to run even at temperature 0,
so compare totals over many questions, not single answers.
"""
import hashlib, json, os, sys, urllib.request
from pathlib import Path

HERE = Path(__file__).parent

def main():
    model, dataset_path = sys.argv[1], sys.argv[2]
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    dry_run = "--dry-run" in sys.argv
    reader = (HERE / "prompts" / "reader.txt").read_text().rstrip("\n")
    dataset = {q["question_id"]: q for q in json.loads(Path(dataset_path).read_text())}
    for line in (HERE / "contexts.jsonl").read_text().splitlines()[:limit]:
        row = json.loads(line)
        q = dataset[row["question_id"]]
        prompt = reader.replace("{context}", row["context"]).replace("{date}", q["question_date"]).replace("{question}", q["question"])
        if dry_run:
            print(row["question_id"], hashlib.sha256(prompt.encode()).hexdigest())
            continue
        body = json.dumps({"model": model, "max_tokens": 1500, "temperature": 0, "messages": [{"role": "user", "content": prompt}]}).encode()
        request = urllib.request.Request("https://api.anthropic.com/v1/messages", body, {"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01", "content-type": "application/json"})
        message = json.loads(urllib.request.urlopen(request).read())
        text = "".join(block.get("text", "") for block in message["content"] if block["type"] == "text").strip()
        print(json.dumps({"question_id": row["question_id"], "question_type": row["question_type"], "hypothesis": text, "model": model, "context_sha256": row["context_sha256"]}))

if __name__ == "__main__":
    main()
