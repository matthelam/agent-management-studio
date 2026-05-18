#!/usr/bin/env bash
# AMS UserPromptSubmit hook — statute anchor + work-intent detection.
#
# Two jobs:
#   1. Inject "statute is loaded" anchor to combat compaction drift.
#   2. Detect work-intent phrases and inject a Jira registration reminder
#      so Claude asks about ticket tracking before diving into changes.
#
# Uses python3 for JSON parsing and regex — no jq dependency.

set -e

CLAUDE_DIR="$CLAUDE_PROJECT_DIR/.claude"
CONFIG="$CLAUDE_DIR/config.json"

INPUT=$(cat)

if ! command -v python3 >/dev/null 2>&1; then
  echo '{"continue": true, "suppressOutput": true, "additionalContext": "Statute is loaded. Patterns, approaches, build/deploy, posture, and standards are in context."}'
  exit 0
fi

_AMS_INPUT="$INPUT" \
_AMS_CONFIG="$CONFIG" \
python3 - <<'PYEOF'
import sys, json, os, re

raw     = os.environ.get('_AMS_INPUT', '')
cfg_path = os.environ.get('_AMS_CONFIG', '')

try:
    data = json.loads(raw)
except Exception:
    data = {}

prompt = data.get('prompt', '')

# ── Statute anchor ────────────────────────────────────────────────────────────
modes = 'fix, change, upgrade, audit'
try:
    with open(cfg_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    mode_keys = list(cfg.get('modes', {}).keys())
    if mode_keys:
        modes = ', '.join(mode_keys)
except Exception:
    pass

anchor = (
    "**Statute is loaded.** Patterns, approaches, build/deploy, posture, and standards "
    "are in the session context. If your work doesn't match any loaded statute, consult "
    f"case-law before improvising. Available delivery modes: {modes}."
)

# ── Work-intent detection ─────────────────────────────────────────────────────
# Phrases that signal the user is starting new delivery work (not asking questions).
WORK_INTENT = re.compile(
    r'\b('
    r'i want to (work on|make a change|add|implement|create|fix|update|modify|refactor|build|delete|remove)|'
    r"i('d| would) like to (work on|make|add|implement|create|fix|change|update)|"
    r'let\'?s (work on|make|add|implement|create|fix|change|update)|'
    r'i need to (work on|make a change|add|implement|create|fix|update|modify)|'
    r'can you (add|implement|create|fix|update|modify|change|delete|remove|build)\b|'
    r'please (add|implement|create|fix|update|modify|change|delete|remove|build)\b|'
    r'make a change to|'
    r'working on a|'
    r'start (a|the) (feature|task|ticket|story|bug|change|fix)'
    r')',
    re.IGNORECASE
)

# Phrases that are clearly NOT delivery work (questions, audit, review).
AUDIT_INTENT = re.compile(
    r'\b(audit|review|explain|what is|how does|tell me|show me|describe|list|find|search|why|where)\b',
    re.IGNORECASE
)

ctx = anchor

if prompt and WORK_INTENT.search(prompt) and not AUDIT_INTENT.search(prompt):
    ctx += (
        "\n\n**WORK-INTENT DETECTED.** Before making any file changes, ask the user: "
        "'Do you have a Jira ticket for this work? If not, I can create one via /deliver-work "
        "to give this a ticket number and register it in the audit trail. Shall I do that first?' "
        "Do NOT start editing files until the user responds. If they confirm /deliver-work, "
        "invoke it now. If they say proceed without a ticket, note it and continue."
    )

print(json.dumps({
    "continue": True,
    "suppressOutput": True,
    "additionalContext": ctx,
}))
PYEOF

exit 0
