#!/usr/bin/env bash
# AMS UserPromptSubmit hook — captures user prompt intent for audit trail.
#
# Stores a PREVIEW (first 250 chars) + LENGTH + SHA256 HASH by default.
# Full prompt text is intentionally NOT stored — prompts may contain secrets,
# personal data, or confidential requirements. The preview + hash is enough
# to correlate intent with downstream tool calls without being a data sink.
#
# Uses python3 for JSON parsing/building — available wherever Node.js is.
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

# Pass the input via env var (avoids stdin-to-heredoc conflicts)
_AMS_INPUT="$INPUT" python3 - <<'PYEOF' | ams-audit emit 2>/dev/null || true
import sys, json, hashlib, os

raw = os.environ.get('_AMS_INPUT', '')
try:
    data = json.loads(raw)
except Exception:
    sys.exit(0)

session = data.get('session_id', '')
prompt  = data.get('prompt', '')

if not prompt:
    sys.exit(0)

LIMIT   = 250
preview = prompt[:LIMIT]
trunc   = len(prompt) > LIMIT
length  = len(prompt)
digest  = hashlib.sha256(prompt.encode('utf-8')).hexdigest()

payload = json.dumps({
    'type':    'prompt_submitted',
    'session': session,
    'payload': {
        'preview':   preview,
        'length':    length,
        'hash':      digest,
        'truncated': trunc,
    }
})
print(payload)
PYEOF

echo '{"continue": true, "suppressOutput": true}'
exit 0
