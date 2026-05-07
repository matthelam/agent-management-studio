#!/usr/bin/env bash
# AMS PreToolUse(Bash) hook — strip AI traces from git/gh commands.
# Deterministic: regex-based; no LLM. Pairs with the `commit-clean` skill which
# provides reasoning. This hook is the guarantee.
#
# Reads tool input from stdin (Claude Code passes a JSON blob with the proposed
# tool call) and emits either pass-through or modified-call JSON.

set -e

# Read input from stdin
INPUT=$(cat)

# Extract the command string. Use jq if available; else grep.
if command -v jq >/dev/null 2>&1; then
  CMD=$(echo "$INPUT" | jq -r '.tool_input.command // ""')
else
  CMD=$(echo "$INPUT" | grep -oP '"command":\s*"\K[^"]*' | head -1 || echo "")
fi

# Only act on git/gh commands that produce committed/published text.
if ! echo "$CMD" | grep -qE '\b(git\s+(commit|tag|notes\s+(add|append|edit))|gh\s+(pr|issue|release)\s+(create|edit|comment))\b'; then
  echo '{"continue": true, "suppressOutput": true}'
  exit 0
fi

# AI-trace patterns to strip (case-insensitive, multiline).
# These are hard rules: never let any of these reach a commit/PR.
STRIPPED="$CMD"

# Co-authored-by Claude / Anthropic / claude code
STRIPPED=$(echo "$STRIPPED" | sed -E 's/Co-Authored-By:[[:space:]]*Claude[^"\\]*//gi')
STRIPPED=$(echo "$STRIPPED" | sed -E 's/Co-Authored-By:[[:space:]]*Anthropic[^"\\]*//gi')

# "Generated with Claude" / "Generated with [Claude Code]" / "Made with Claude"
STRIPPED=$(echo "$STRIPPED" | sed -E 's/(Generated|Made|Created|Authored)[[:space:]]+with[[:space:]]+\[?Claude[^"\\]*\]?[^"\\]*//gi')

# Robot emoji (🤖 / :robot:)
STRIPPED=$(echo "$STRIPPED" | sed 's/🤖//g')
STRIPPED=$(echo "$STRIPPED" | sed -E 's/:robot[^:]*://g')

# Direct claude / anthropic mentions in commit-message context (heuristic)
STRIPPED=$(echo "$STRIPPED" | sed -E 's/by[[:space:]]+Claude[[:space:]]+(Code|Sonnet|Opus|Haiku|Agent)[[:space:]]*//gi')

# Trailing whitespace / empty lines created by stripping
STRIPPED=$(echo "$STRIPPED" | sed -E 's/[[:space:]]+$//')

if [ "$STRIPPED" = "$CMD" ]; then
  # No change — pass through.
  echo '{"continue": true, "suppressOutput": true}'
  exit 0
fi

# Emit modified tool input + a system note (visible to the dev).
if command -v jq >/dev/null 2>&1; then
  jq -n --arg cmd "$STRIPPED" '{
    "continue": true,
    "suppressOutput": false,
    "modifyToolInput": {"command": $cmd},
    "systemMessage": "commit-clean: stripped AI-trace markers from git/gh command. The active ticket reference (if any) should be embedded by the deliver-work skill."
  }'
else
  printf '{"continue": true, "suppressOutput": false, "modifyToolInput": {"command": "%s"}, "systemMessage": "commit-clean: stripped AI-trace markers."}\n' "${STRIPPED//\"/\\\"}"
fi
exit 0
