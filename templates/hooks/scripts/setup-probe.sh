#!/usr/bin/env bash
# AMS Setup hook — verify claude-mem worker reachable; emit guidance if not.
# Order-independent: probes only; does not depend on claude-mem's own Setup hook.

set -e

WORKER_HOST="${CLAUDE_MEM_WORKER_HOST:-127.0.0.1}"
WORKER_PORT="${CLAUDE_MEM_WORKER_PORT:-37777}"
HEALTH_URL="http://${WORKER_HOST}:${WORKER_PORT}/api/health"

if curl -sf --max-time 2 "$HEALTH_URL" >/dev/null 2>&1; then
  # Worker reachable — proceed silently.
  echo '{"continue": true, "suppressOutput": true}'
  exit 0
fi

# Worker unreachable — surface remediation.
cat <<'EOF'
{
  "continue": true,
  "suppressOutput": false,
  "systemMessage": "AMS preflight: claude-mem worker not reachable at http://127.0.0.1:37777. Run `npx claude-mem start` in a separate terminal. Without claude-mem, behavioural-drift queries (used by the `update` skill) will be unavailable. The session can proceed with prescriptive-only context."
}
EOF
exit 0
