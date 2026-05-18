#!/usr/bin/env bash
# AMS PreToolUse(*) hook — load prescriptive-rules.json and hard-block any tool
# call matching a rule in the blocklist.
# Zero LLM. Sub-millisecond. Uses python3 (no jq dependency).
#
# prescriptive-rules.json schema:
# {
#   "version": 1,
#   "rules": [
#     {
#       "id": "serialized-items-scs-managed",
#       "tools": ["Edit", "Write"],
#       "match": {"path_glob": "src/serialization/**"},
#       "action": "block",
#       "reason": "GUARD RAIL: ..."
#     }
#   ]
# }

set -e

CLAUDE_DIR="$CLAUDE_PROJECT_DIR/.claude"
RULES_FILE="$CLAUDE_DIR/prescriptive-rules.json"

if [ ! -f "$RULES_FILE" ]; then
  echo '{"continue": true, "suppressOutput": true}'
  exit 0
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo '{"continue": true, "suppressOutput": true}'
  exit 0
fi

INPUT=$(cat)

_AMS_INPUT="$INPUT" \
_AMS_RULES="$RULES_FILE" \
_AMS_PROJECT="$CLAUDE_PROJECT_DIR" \
python3 - <<'PYEOF'
import sys, json, os, re

raw        = os.environ.get('_AMS_INPUT', '')
rules_path = os.environ.get('_AMS_RULES', '')
project    = os.environ.get('_AMS_PROJECT', '').replace('\\', '/')

try:
    data = json.loads(raw)
except Exception:
    print(json.dumps({"continue": True, "suppressOutput": True}))
    sys.exit(0)

try:
    with open(rules_path, 'r', encoding='utf-8') as f:
        rules_doc = json.load(f)
except Exception:
    print(json.dumps({"continue": True, "suppressOutput": True}))
    sys.exit(0)

tool_name  = data.get('tool_name', '')
tool_input = data.get('tool_input', {}) or {}

def glob_to_regex(pattern):
    """Convert a path glob (with ** and *) to a regex string."""
    regex = ''
    i = 0
    while i < len(pattern):
        if pattern[i:i+2] == '**':
            regex += '.*'
            i += 2
            # consume optional trailing slash after **
            if i < len(pattern) and pattern[i] == '/':
                i += 1
        elif pattern[i] == '*':
            regex += '[^/]*'
            i += 1
        elif pattern[i] == '?':
            regex += '[^/]'
            i += 1
        elif pattern[i] in r'\.^$+{}[]|()'  :
            regex += '\\' + pattern[i]
            i += 1
        else:
            regex += pattern[i]
            i += 1
    return regex

def normalise(path):
    """Normalise to forward slashes; strip project dir prefix if present."""
    p = path.replace('\\', '/')
    if project and p.startswith(project):
        p = p[len(project):].lstrip('/')
    return p

for rule in rules_doc.get('rules', []):
    rule_id   = rule.get('id', '')
    tools     = rule.get('tools', [])
    action    = rule.get('action', '')
    match     = rule.get('match', {})
    reason    = rule.get('reason', '')

    # Tool filter (empty tools list = applies to all)
    if tools and tool_name not in tools:
        continue

    hit = False

    # path_glob — match against file_path or path in tool_input
    path_glob = match.get('path_glob', '')
    if path_glob:
        raw_path = tool_input.get('file_path') or tool_input.get('path', '')
        if raw_path:
            norm = normalise(raw_path)
            regex = glob_to_regex(path_glob)
            # Try anchored match on relative path, then substring match as fallback
            if re.fullmatch(regex, norm) or re.search(regex, norm):
                hit = True

    # command_regex — match against command in tool_input (Bash tool)
    cmd_regex = match.get('command_regex', '')
    if cmd_regex:
        cmd = tool_input.get('command', '')
        if cmd and re.search(cmd_regex, cmd):
            hit = True

    if hit and action == 'block':
        print(json.dumps({
            "continue": False,
            "suppressOutput": False,
            "stopReason": f"AMS GUARD RAIL [{rule_id}]: {reason}",
        }))
        sys.exit(0)

    if hit and action == 'warn':
        # Warn mode: allow but inject a system message
        print(json.dumps({
            "continue": True,
            "suppressOutput": False,
            "systemMessage": f"AMS WARNING [{rule_id}]: {reason}",
        }))
        sys.exit(0)

print(json.dumps({"continue": True, "suppressOutput": True}))
PYEOF

exit 0
