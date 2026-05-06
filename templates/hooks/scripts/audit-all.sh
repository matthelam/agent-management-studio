#!/usr/bin/env bash
# AMS PostToolUse(*) hook — deterministic audit logger.
# Fires after EVERY tool call. Classifies tool_name + input → typed event,
# then pipes a JSON payload to `ams-audit emit` (stdin mode).
#
# Design: zero LLM, sub-millisecond. Never blocks (always returns continue:true).
# Uses python3 for JSON parsing/building — available wherever Node.js is.
# Silently no-ops if ams-audit is not installed — does not break tool execution.
#
# Install: registered via .claude/settings.json PostToolUse hook on matcher "*".

set -e

if ! command -v ams-audit >/dev/null 2>&1; then
  echo '{"continue": true, "suppressOutput": true}'
  exit 0
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo '{"continue": true, "suppressOutput": true}'
  exit 0
fi

INPUT=$(cat)

_AMS_INPUT="$INPUT" python3 - <<'PYEOF' | ams-audit emit 2>/dev/null || true
import sys, json, os, re

raw = os.environ.get('_AMS_INPUT', '')
try:
    data = json.loads(raw)
except Exception:
    sys.exit(0)

tool    = data.get('tool_name', '')
session = data.get('session_id', '')
inp     = data.get('tool_input', {}) or {}
resp    = data.get('tool_response', {}) or {}

event_type = ''
payload    = {}

if tool == 'Read':
    event_type = 'file_read'
    payload    = {'file': inp.get('file_path', '')}

elif tool == 'Write':
    event_type = 'artifact_write'
    payload    = {
        'file':  inp.get('file_path', ''),
        'bytes': resp.get('bytesWritten', 0),
    }

elif tool == 'Edit':
    event_type = 'artifact_edit'
    payload    = {'file': inp.get('file_path', '')}

elif tool in ('Glob', 'Grep'):
    event_type = 'file_search'
    payload    = {'pattern': inp.get('pattern') or inp.get('query', '')}

elif tool in ('WebFetch', 'WebSearch'):
    event_type = 'web_fetch'
    payload    = {'url': inp.get('url') or inp.get('query', '')}

elif tool == 'Agent':
    event_type = 'agent_spawn'
    payload    = {
        'description':   inp.get('description', ''),
        'subagent_type': inp.get('subagent_type', ''),
    }

elif tool == 'Bash':
    cmd = (inp.get('command', '') or '')[:200]

    if re.search(r'\bgit\s+commit\b', cmd):
        m   = re.search(r'-m\s+"([^"]*)"', cmd)
        msg = (m.group(1) if m else '')[:72]
        event_type = 'git_commit'
        payload    = {'msg_preview': msg}

    elif re.search(r'\bgit\s+push\b', cmd):
        event_type = 'git_push'
        payload    = {'command': cmd}

    elif re.search(r'\bgit\s+(checkout|switch|branch)\b', cmd):
        event_type = 'git_branch'
        payload    = {'command': cmd}

    elif re.search(r'\bgit\b', cmd):
        event_type = 'git_operation'
        payload    = {'command': cmd}

    elif re.search(r'\b(npm|bun|pnpm|yarn)\b', cmd):
        event_type = 'npm_operation'
        payload    = {'command': cmd}

    elif re.search(r'\b(dotnet|msbuild)\b', cmd):
        event_type = 'dotnet_operation'
        payload    = {'command': cmd}

    elif re.search(r'\b(curl|wget)\b', cmd):
        m   = re.search(r'https?://\S+', cmd)
        url = m.group(0) if m else ''
        event_type = 'http_request'
        payload    = {'command': cmd, 'url': url}

    else:
        event_type = 'bash_operation'
        payload    = {'command': cmd}

else:
    event_type = 'tool_use'
    payload    = {'tool': tool}

if event_type:
    print(json.dumps({
        'type':    event_type,
        'session': session,
        'payload': payload,
    }))
PYEOF

echo '{"continue": true, "suppressOutput": true}'
exit 0
