#!/usr/bin/env bash
# AMS UserPromptSubmit hook — lightweight anchor + mode classification.
# Combats compaction drift; cheap (~20-50 tokens of injected text).

set -e

CLAUDE_DIR="$CLAUDE_PROJECT_DIR/.claude"
CONFIG="$CLAUDE_DIR/config.json"

# Read mode list from config.json if present.
MODES="fix, change, upgrade, audit"
if [ -f "$CONFIG" ] && command -v jq >/dev/null 2>&1; then
  MODE_KEYS=$(jq -r '.modes | keys | join(", ")' "$CONFIG" 2>/dev/null || echo "")
  [ -n "$MODE_KEYS" ] && MODES="$MODE_KEYS"
fi

ANCHOR="**Statute is loaded.** Patterns, approaches, build/deploy, posture, and standards are in the session context. If your work doesn't match any loaded statute, run \`mem-search\` to consult case-law before improvising. Available delivery modes: ${MODES}."

if command -v jq >/dev/null 2>&1; then
  jq -n --arg ctx "$ANCHOR" '{"continue": true, "suppressOutput": true, "additionalContext": $ctx}'
else
  printf '{"continue": true, "suppressOutput": true, "additionalContext": "%s"}\n' "$ANCHOR"
fi
exit 0
