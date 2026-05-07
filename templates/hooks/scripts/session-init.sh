#!/usr/bin/env bash
# AMS SessionStart hook — inject prescriptive layer + reconcile prior session_summaries.
# Self-anchoring: produces complete framing regardless of order vs claude-mem's hooks.

set -e

CLAUDE_DIR="$CLAUDE_PROJECT_DIR/.claude"
POSTURE="$CLAUDE_DIR/posture.md"
PATTERNS="$CLAUDE_DIR/patterns.md"
APPROACHES="$CLAUDE_DIR/approaches.md"
BUILD_DEPLOY="$CLAUDE_DIR/build-deploy.md"
CONFIG="$CLAUDE_DIR/config.json"

# Build the injection. Skip files that don't exist (graceful when learn-codebase
# hasn't fully seeded yet).

INJECTION=""

if [ -f "$POSTURE" ]; then
  INJECTION+="# Posture (universal — every action)"$'\n'
  INJECTION+="$(cat "$POSTURE")"$'\n\n'
fi

if [ -f "$PATTERNS" ]; then
  INJECTION+="# Project Patterns (statute)"$'\n'
  INJECTION+="$(cat "$PATTERNS")"$'\n\n'
fi

if [ -f "$APPROACHES" ]; then
  INJECTION+="# Project Approaches (statute)"$'\n'
  INJECTION+="$(cat "$APPROACHES")"$'\n\n'
fi

if [ -f "$BUILD_DEPLOY" ]; then
  INJECTION+="# Build & Deploy (canonical commands)"$'\n'
  INJECTION+="$(cat "$BUILD_DEPLOY")"$'\n\n'
fi

# Self-anchoring frame — works regardless of claude-mem hook ordering.
INJECTION+="# Working Frame"$'\n'
INJECTION+="The above prescriptive layer is statute for this project. Where statute is silent or ambiguous, consult claude-mem (use \`mem-search\`) for case-law (prior session evidence) before improvising. Common law informs amendments to statute via the \`update\` skill — it does not override statute unilaterally."$'\n'

# Emit as additional context. JSON-escape via jq if available, else fall back.
if command -v jq >/dev/null 2>&1; then
  jq -n --arg ctx "$INJECTION" '{"continue": true, "suppressOutput": true, "additionalContext": $ctx}'
else
  # Minimal fallback — escape backslashes and double quotes
  ESCAPED=$(printf '%s' "$INJECTION" | sed 's/\\/\\\\/g; s/"/\\"/g; ':a;N;$!ba;s/\n/\\n/g')
  printf '{"continue": true, "suppressOutput": true, "additionalContext": "%s"}\n' "$ESCAPED"
fi
exit 0
