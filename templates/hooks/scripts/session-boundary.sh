#!/usr/bin/env bash
# AMS SessionStart + Stop hook — logs session lifecycle events.
#
# Registered on two events:
#   SessionStart  → emits session_start
#   Stop          → emits session_end
#
# The hook_event_name field in stdin distinguishes which event fired.
# Uses python3 for JSON parsing — available wherever Node.js is.
# Silently no-ops if ams-audit or python3 not installed.

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
import sys, json, os

raw = os.environ.get('_AMS_INPUT', '')
try:
    data = json.loads(raw)
except Exception:
    sys.exit(0)

hook_event = data.get('hook_event_name', '')
session    = data.get('session_id', '')
source     = data.get('source', '')  # startup|resume|clear|compact

if hook_event == 'SessionStart':
    out = json.dumps({
        'type':    'session_start',
        'session': session,
        'payload': {'source': source},
    })
elif hook_event == 'Stop':
    out = json.dumps({
        'type':    'session_end',
        'session': session,
        'payload': {},
    })
else:
    sys.exit(0)

print(out)
PYEOF

echo '{"continue": true, "suppressOutput": true}'
exit 0
