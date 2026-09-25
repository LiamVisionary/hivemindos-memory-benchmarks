#!/usr/bin/env node
/**
 * LoCoMo held-out run: does a version of `hive-brain answer` generalise to a dataset it was never tuned on?
 *
 * Development only. The same question sample, reader, reading prompt and judge for every code version; only the memory
 * code differs (run this file from a checkout of each version). The reading and judging prompts are Mem0's pinned
 * LoCoMo prompts (mem0ai/memory-benchmarks, rendered to JSON beforehand with their source file's sha256).
 *
 *   sample    the pre-registered question sample: per category, the questions with the lowest
 *             sha256("<seed>:<conversation>:<question index>"), in proportion to the category's size. No network.
 *   retrieve  one vault per conversation through the product's own conversation archive and full-vault index, then
 *             every sampled question put to memory as a question (`hive-brain answer`'s path). No network, no spend.
 *   answer    reader through Anthropic's Message Batches API, judge on OpenAI's own API.
 *   score     paired accuracy between two runs' answers, with an exact McNemar test.
 *
 *   node scripts/benchmark-locomo-heldout.mjs sample --dataset locomo10.json --seed <seed> --size 500 --out sample.json
 *   node scripts/benchmark-locomo-heldout.mjs retrieve --dataset locomo10.json --sample sample.json --out <dir> [--speakers user-assistant|both-user]
 *   passbook run --only ANTHROPIC_API_KEY --only OPENAI_API_KEY -- node scripts/benchmark-locomo-heldout.mjs answer --out <dir> --prompts mem0-locomo-prompts.json --reader claude-opus-4-6 --judge gpt-4o-2024-08-06
 *   node scripts/benchmark-locomo-heldout.mjs score --runs <dirA>,<dirB> --label opus
 */
import { createHash } from "node:crypto";
import { existsSync } from "node:fs";
import { mkdtemp, readFile, readdir, rm, writeFile } from "node:fs/promises";
import { register } from "node:module";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

import { openAiDirectChat, pool, runAnthropicBatch, writeJsonAtomic } from "./lib/benchmark-llm.mjs";
import { cliAnswerText } from "./lib/longmemeval-arms.mjs";
import { locomoSessions, parseLocomoDate } from "./lib/standard-memory-benchmark.mjs";

register(new URL("./lib/ts-relative-loader.mjs", import.meta.url));

function parseArgs(argv) {
  const args = { phase: argv[0], concurrency: 4, readerMaxTokens: 1500, speakers: "user-assistant" };
  for (let index = 1; index < argv.length; index += 2) {
    const key = argv[index].replace(/^--/, "").replace(/-([a-z])/g, (_, letter) => letter.toUpperCase());
    args[key] = argv[index + 1];
  }
  if (!["sample", "retrieve", "answer", "score"].includes(args.phase)) throw new Error("First argument must be sample, retrieve, answer or score");
  return args;
}

const questionId = (conversation, index) => `conv${conversation}-q${index}`;

async function samplePhase(args) {
  const dataset = JSON.parse(await readFile(resolve(args.dataset), "utf8"));
  const prompts = args.prompts ? JSON.parse(await readFile(resolve(args.prompts), "utf8")) : null;
  const categories = prompts?.categories ?? [1, 2, 3, 4];
  const byCategory = new Map(categories.map((category) => [category, []]));
  dataset.forEach((entry, conversation) => (entry.qa ?? []).forEach((qa, index) => {
    if (!byCategory.has(qa.category)) return;
    byCategory.get(qa.category).push({ id: questionId(conversation, index), key: createHash("sha256").update(`${args.seed}:${conversation}:${index}`).digest("hex") });
  }));
  const eligible = [...byCategory.values()].reduce((sum, items) => sum + items.length, 0);
  const size = Number(args.size);
  const ids = [];
  for (const [category, items] of byCategory) {
    const take = Math.round(size * items.length / eligible);
    ids.push(...items.sort((left, right) => left.key.localeCompare(right.key)).slice(0, take).map((item) => item.id));
    console.log(`category ${category}: ${take} of ${items.length}`);
  }
  await writeFile(resolve(args.out), `${JSON.stringify({ seed: args.seed, eligible, ids: ids.sort() }, null, 1)}\n`, "utf8");
  console.log(`${ids.length} questions -> ${args.out}`);
}

async function retrievePhase(args) {
  const { syncConversationNoteForSession } = await import("../src/lib/services/obsidian/conversation-notes.ts");
  const { answerFromAgentMemory } = await import("../src/lib/services/obsidian/agent-memory/core.ts");
  const { rebuildFullVaultSearchIndex } = await import("../src/lib/services/obsidian/full-vault-search-index.ts");
  const dataset = JSON.parse(await readFile(resolve(args.dataset), "utf8"));
  const wanted = new Set(JSON.parse(await readFile(resolve(args.sample), "utf8")).ids);
  const out = join(resolve(args.out), "retrieval");
  let written = 0;
  for (const [conversation, entry] of dataset.entries()) {
    const questions = (entry.qa ?? []).map((qa, index) => ({ qa, id: questionId(conversation, index) })).filter(({ id }) => wanted.has(id) && !existsSync(join(out, `${id}.json`)));
    if (!questions.length) continue;
    const sessions = locomoSessions(entry);
    const root = await mkdtemp(join(tmpdir(), "locomo-heldout-"));
    for (const session of sessions) {
      const messages = session.messages.map((message) => ({ ...message, role: args.speakers === "both-user" ? "user" : message.role }));
      await syncConversationNoteForSession({ id: `locomo-${conversation}-${session.id}`, sessionId: `locomo-${conversation}-${session.id}`, runtime: "locomo-heldout-benchmark", source: "hivemindos-chat", agentId: "locomo-heldout-benchmark", agentName: "Assistant", sharedVaultPath: root, startedAt: session.startedAt, updatedAt: session.startedAt + messages.length * 1_000, endedAt: session.startedAt + messages.length * 1_000, endReason: "benchmark-fixture-complete", messages: messages.map((message, index) => ({ index, role: message.role, content: message.content, createdAt: session.startedAt + index * 1_000 })) });
    }
    await rebuildFullVaultSearchIndex({ root });
    // Mem0's reference date: the last session's date as the dataset writes it; "today" for memory is the same moment.
    const last = sessions.at(-1);
    const now = new Date(parseLocomoDate(last.date) ?? last.startedAt).toISOString();
    await pool(questions, Number(args.concurrency), async ({ qa, id }) => {
      const result = await answerFromAgentMemory({ vaultPath: root, query: String(qa.question), limit: 5, trackUsage: false, evidenceBudget: "question", now });
      const context = cliAnswerText(result);
      await writeJsonAtomic(join(out, `${id}.json`), { questionId: id, conversation, category: qa.category, question: String(qa.question), answer: String(qa.answer ?? ""), evidence: qa.evidence ?? [], referenceDate: last.date, now, speakers: args.speakers, context, contextSha256: createHash("sha256").update(context).digest("hex") });
      written += 1;
    });
    await rm(root, { recursive: true, force: true });
    console.log(`conversation ${conversation}: ${questions.length} questions`);
  }
  console.log(`retrieval complete: ${written} written in ${out}`);
}

async function answerPhase(args) {
  const prompts = JSON.parse(await readFile(resolve(args.prompts), "utf8"));
  const root = resolve(args.out);
  const label = args.label ?? args.reader;
  const rows = [];
  for (const file of (await readdir(join(root, "retrieval"))).filter((name) => name.endsWith(".json")).sort()) rows.push(JSON.parse(await readFile(join(root, "retrieval", file), "utf8")));
  const jobs = rows.filter((row) => !existsSync(join(root, "answers", label, `${row.questionId}.json`)));
  if (!jobs.length) return console.log("nothing to answer");
  // Mem0's answer prompt, its three placeholders filled; our memory's answer stands where Mem0 lists its memories.
  const prompt = (row) => prompts.answer_prompt.replace("{reference_date}", () => row.referenceDate).replace("{memories}", () => row.context).replace("{question}", () => row.question);
  const replies = await runAnthropicBatch({ out: root, name: `reader-${label}`, model: args.reader, requests: jobs.map((row) => ({ custom_id: row.questionId, params: { model: args.reader, max_tokens: Number(args.readerMaxTokens), temperature: 0, messages: [{ role: "user", content: prompt(row) }] } })) });
  let written = 0;
  await pool(jobs.filter((row) => replies.get(row.questionId)?.text), Number(args.concurrency), async (row) => {
    const reply = replies.get(row.questionId);
    const generated = reply.text.includes("ANSWER:") ? reply.text.split("ANSWER:").at(-1).trim() : reply.text;
    // Mem0: an open-domain gold answer is judged on its first part (before ";").
    const gold = row.category === 3 && row.answer.includes(";") ? row.answer.split(";")[0].trim() : row.answer;
    const judgePrompt = prompts.judge_prompt.replace("{question}", () => row.question).replace("{answer}", () => gold).replace("{response}", () => generated);
    const judged = await openAiDirectChat({ model: args.judge, system: prompts.judge_system, prompt: judgePrompt, maxTokens: 200, json: true });
    let verdict = "";
    try { verdict = String(JSON.parse(judged.text).label ?? "").toUpperCase(); } catch { verdict = /\bCORRECT\b/.test(judged.text) && !/\bWRONG\b/.test(judged.text) ? "CORRECT" : "WRONG"; }
    await writeJsonAtomic(join(root, "answers", label, `${row.questionId}.json`), { questionId: row.questionId, category: row.category, contextSha256: row.contextSha256, reader: { model: args.reader, text: reply.text, answer: generated, usage: reply.usage, cost: reply.cost }, judge: { model: judged.model, text: judged.text }, correct: verdict === "CORRECT" });
    written += 1;
  });
  console.log(`answer: ${written}/${jobs.length} written; ${jobs.length - [...replies.values()].filter((reply) => reply?.text).length} unanswered`);
}

function exactMcNemar(onlyA, onlyB) {
  const n = onlyA + onlyB;
  if (!n) return 1;
  let tail = 0;
  let term = 1 / 2 ** n;
  for (let k = 0; k <= Math.min(onlyA, onlyB); k += 1) {
    tail += term;
    term = term * (n - k) / (k + 1);
  }
  return Math.min(1, 2 * tail);
}

async function scorePhase(args) {
  const [first, second] = args.runs.split(",").map((dir) => resolve(dir));
  const load = async (dir) => {
    const answers = new Map();
    const folder = join(dir, "answers", args.label);
    for (const file of (await readdir(folder)).filter((name) => name.endsWith(".json"))) {
      const row = JSON.parse(await readFile(join(folder, file), "utf8"));
      answers.set(row.questionId, row);
    }
    return answers;
  };
  const [a, b] = [await load(first), await load(second)];
  const ids = [...a.keys()].filter((id) => b.has(id)).sort();
  const report = { paired: ids.length, runs: [first, second], overall: {}, byCategory: {} };
  const tally = (subset) => {
    const onlyA = subset.filter((id) => a.get(id).correct && !b.get(id).correct).length;
    const onlyB = subset.filter((id) => b.get(id).correct && !a.get(id).correct).length;
    return { questions: subset.length, first: subset.filter((id) => a.get(id).correct).length, second: subset.filter((id) => b.get(id).correct).length, onlyFirst: onlyA, onlySecond: onlyB, p: Number(exactMcNemar(onlyA, onlyB).toFixed(4)) };
  };
  report.overall = tally(ids);
  for (const category of [...new Set(ids.map((id) => a.get(id).category))].sort()) report.byCategory[category] = tally(ids.filter((id) => a.get(id).category === category));
  console.log(JSON.stringify(report, null, 2));
}

const args = parseArgs(process.argv.slice(2));
await { sample: samplePhase, retrieve: retrievePhase, answer: answerPhase, score: scorePhase }[args.phase](args);
