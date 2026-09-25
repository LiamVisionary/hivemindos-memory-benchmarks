#!/bin/bash
# Sibyl's runner spawns `claude`; this runs Claude Code 2.1.280 with Opus 4.6 in an empty HOME (no user settings, hooks
# or CLAUDE.md), logs the JSON result (cost, turns) and prints the answer text as the runner expects.
REAL="$HOME_REAL/Library/Application Support/Claude/claude-code/2.1.280/claude.app/Contents/MacOS/claude"
out=$(HOME="$ISO_HOME" "$REAL" --model claude-opus-4-6 --output-format json "$@")
code=$?
printf '%s\n' "$out" | tr -d '\n' >> "$COST_LOG"; printf '\n' >> "$COST_LOG"
printf '%s' "$out" | python3 -c 'import json,sys
try: print(json.loads(sys.stdin.read()).get("result",""))
except Exception: pass'
exit $code
