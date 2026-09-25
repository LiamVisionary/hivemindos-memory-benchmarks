#!/usr/bin/env python3
"""
Grade any hypotheses file again with LongMemEval's official judge, on your own OpenAI key (about $1 for 500 answers).

  OPENAI_API_KEY=... python3 regrade.py opus-4.6/hypotheses.jsonl path/to/longmemeval_oracle.json [--limit N]

Sibyl-Memory's own answer files (github.com/Sibyl-Labs/memory-bench-kit, longmemeval/results/) have the same fields and
can be graded the same way. The prompts are in prompts/judge.mjs; this is the same text, ported.
"""
import json, os, sys, urllib.request
from pathlib import Path

def judge_prompt(qtype, question, answer, response, abstention):
    if abstention:
        return f"I will give you an unanswerable question, an explanation, and a response from a model. Please answer yes if the model correctly identifies the question as unanswerable. The model could say that the information is incomplete, or some other information is given but the asked information is not.\n\nQuestion: {question}\n\nExplanation: {answer}\n\nModel Response: {response}\n\nDoes the model correctly identify the question as unanswerable? Answer yes or no only."
    if qtype in ("single-session-user", "single-session-assistant", "multi-session"):
        return f"I will give you a question, a correct answer, and a response from a model. Please answer yes if the response contains the correct answer. Otherwise, answer no. If the response is equivalent to the correct answer or contains all the intermediate steps to get the correct answer, you should also answer yes. If the response only contains a subset of the information required by the answer, answer no. \n\nQuestion: {question}\n\nCorrect Answer: {answer}\n\nModel Response: {response}\n\nIs the model response correct? Answer yes or no only."
    if qtype == "temporal-reasoning":
        return f"I will give you a question, a correct answer, and a response from a model. Please answer yes if the response contains the correct answer. Otherwise, answer no. If the response is equivalent to the correct answer or contains all the intermediate steps to get the correct answer, you should also answer yes. If the response only contains a subset of the information required by the answer, answer no. In addition, do not penalize off-by-one errors for the number of days. If the question asks for the number of days/weeks/months, etc., and the model makes off-by-one errors (e.g., predicting 19 days when the answer is 18), the model's response is still correct. \n\nQuestion: {question}\n\nCorrect Answer: {answer}\n\nModel Response: {response}\n\nIs the model response correct? Answer yes or no only."
    if qtype == "knowledge-update":
        return f"I will give you a question, a correct answer, and a response from a model. Please answer yes if the response contains the correct answer. Otherwise, answer no. If the response contains some previous information along with an updated answer, the response should be considered as correct as long as the updated answer is the required answer.\n\nQuestion: {question}\n\nCorrect Answer: {answer}\n\nModel Response: {response}\n\nIs the model response correct? Answer yes or no only."
    return f"I will give you a question, a rubric for desired personalized response, and a response from a model. Please answer yes if the response satisfies the desired response. Otherwise, answer no. The model does not need to reflect all the points in the rubric. The response is correct as long as it recalls and utilizes the user's personal information correctly.\n\nQuestion: {question}\n\nRubric: {answer}\n\nModel Response: {response}\n\nIs the model response correct? Answer yes or no only."

def main():
    hypotheses_path, dataset_path = sys.argv[1], sys.argv[2]
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    dataset = {q["question_id"]: q for q in json.loads(Path(dataset_path).read_text())}
    rows = [json.loads(line) for line in Path(hypotheses_path).read_text().splitlines() if line][:limit]
    right = 0
    for row in rows:
        q = dataset[row["question_id"]]
        body = json.dumps({"model": "gpt-4o-2024-08-06", "temperature": 0, "max_tokens": 10, "messages": [{"role": "user", "content": judge_prompt(q["question_type"], q["question"], q["answer"], row["hypothesis"], q["question_id"].endswith("_abs"))}]}).encode()
        request = urllib.request.Request("https://api.openai.com/v1/chat/completions", body, {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}", "Content-Type": "application/json"})
        verdict = json.loads(urllib.request.urlopen(request).read())["choices"][0]["message"]["content"]
        ok = "yes" in verdict.lower()
        right += ok
        print(json.dumps({"question_id": q["question_id"], "question_type": q["question_type"], "judge_output": verdict, "correct": ok}))
    print(f"# {right}/{len(rows)} graded correct", file=sys.stderr)

if __name__ == "__main__":
    main()
