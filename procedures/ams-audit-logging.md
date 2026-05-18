# AMS-Side Audit Logging

Every AMS-only skill (`learn-codebase`, `curate-tools`, future skills) emits a
structured run log to `<ams-root>/logs/<skill>-<run-id>.jsonl`.

This is **distinct** from target-side audit logging (`procedures/audit-logging.md`,
seeded into targets at `.claude/audit/`). AMS-side logs capture what AMS *did*
to a target during seeding/maintenance. Target-side logs capture what a seeded
agent did *inside* the target during normal work.

The two never share files. They have different schemas and different lifecycles.

---

## Why this exists

When learn-codebase fails partially or silently — gitignore not written, claude-mem
unreachable, SDK overload, project-ID mismatch — filesystem forensics is a poor
debugging tool. A structured run log captures every step boundary, every
external dependency check, every file write, every error, with timestamps and
correlation IDs.

A bug visible in the log is a debuggable bug. A bug visible only in
"some files exist, some don't" is a research project.

---

## Where logs live

```
<ams-root>/logs/
  learn-codebase-2026-05-06T20-32-15-<run-id>.jsonl
  curate-tools-2026-05-06T18-04-22-<run-id>.jsonl
```

- One file per skill invocation.
- Filename: `<skill>-<iso-timestamp-no-colons>-<run-id>.jsonl`
- `<run-id>`: UUIDv4 generated at invocation start.
- Format: JSONL — one JSON event per line, append-only.

The `logs/` directory is gitignored at the AMS repo level (AMS itself can
gitignore freely; the no-AI-footprint rule applies to *target* repos, not to AMS).

---

## Event schema

Every event has these required fields:

```json
{
  "timestamp": "2026-05-06T20:32:15.123Z",
  "run_id": "<uuid-v4>",
  "skill": "learn-codebase",
  "event_type": "<see taxonomy below>",
  "level": "info | warn | error",
  "step": "<step-id-or-name | null>",
  "payload": { /* event-specific */ }
}
```

Optional fields per event type:
- `target` — absolute path of the target repo (learn-codebase only)
- `duration_ms` — for `step_end` and `invocation_end`
- `error` — for `error` level events: `{ "name": "...", "message": "...", "stack": "..." | null }`

---

## Event taxonomy

### Lifecycle events (every skill)

| `event_type` | When emitted | Required payload |
|---|---|---|
| `invocation_start` | First action of skill | `args`, `cwd`, `ams_version`, `claude_mem_version` (if probed) |
| `invocation_end` | Final action of skill | `outcome: "success" \| "failure" \| "stopped"`, `duration_ms`, `summary: { /* skill-specific tallies */ }` |
| `step_start` | At the start of each numbered step | `step_id`, `step_name` |
| `step_end` | At the end of each numbered step | `step_id`, `step_name`, `outcome`, `duration_ms` |

### Dependency check events

| `event_type` | When emitted | Required payload |
|---|---|---|
| `dependency_probe` | Any check on an external dependency | `dependency: "claude-mem" \| "bun" \| "node" \| "git" \| "<cli>" \| "<mcp>"`, `outcome: "reachable" \| "unreachable" \| "version_mismatch"`, `details: {...}` |
| `dependency_remediation` | When a probe fails and remediation is offered/taken | `dependency`, `action_proposed`, `action_taken`, `human_decision` |

### File-write events (the audit trail for "what got seeded where")

| `event_type` | When emitted | Required payload |
|---|---|---|
| `artifact_write` | Every file written into the target (or AMS) | `path`, `bytes`, `sha256`, `intent: "seed" \| "generate" \| "update" \| "config"` |
| `artifact_skip` | When a write was planned but skipped | `path`, `reason` |
| `gitignore_update` | The `.git/info/exclude` write (Step 11 of learn-codebase) | `target`, `entries_added`, `entries_already_present` |

### Analysis events (learn-codebase specific)

| `event_type` | When emitted | Required payload |
|---|---|---|
| `stack_detected` | After Step 2 | `runtime`, `frameworks`, `solution_type`, `framework_count` |
| `build_deploy_resolved` | After Step 3 | `canonical_build`, `canonical_test`, `canonical_deploy`, `conflicts: [...]` |
| `cognitive_team_proposed` | During Step 4 | `harnesses`, `lenses`, `primary_for_single`, `audit_primary` |
| `cognitive_team_approved` | After dev review of Step 4 | `harnesses_accepted`, `harnesses_rejected`, `harnesses_modified` |
| `domain_skill_generated` | Per-tech, during Step 4b | `tech`, `skill_name`, `bytes`, `sections: [...]` |
| `assembly_manifest_written` | After Step 5 | `team_size`, `domain_skill_count`, `lens_count` |
| `pattern_detected` | Per pattern, Step 6 | `category`, `rule_count` |
| `approach_detected` | Per approach, Step 7 | `category`, `guard_rail_count` |
| `prescriptive_rule_generated` | Per rule, Step 8 | `rule_id`, `tools`, `match_type` |

### Claude-mem interaction events (the project-ID issue would have surfaced here)

| `event_type` | When emitted | Required payload |
|---|---|---|
| `claude_mem_observation_seeded` | Per synthetic observation in Step 12 | `observation_type`, `project: "<target-id>"`, `narrative_length`, `concepts: [...]` |
| `claude_mem_observation_failed` | When a synthetic observation POST fails | `observation_type`, `error`, `retry_attempted` |
| `claude_mem_project_id_resolved` | Once at start, after probing | `auto_detected_id`, `target_basename`, `id_will_be_used`, `reason` |

### Curate-tool specific

| `event_type` | When emitted | Required payload |
|---|---|---|
| `harness_check` | Each automated harness check | `dimension`, `outcome`, `score`, `notes` |
| `manual_harness_check` | Each curator-walked check | `dimension`, `outcome`, `curator_notes` |
| `gap_identified` | Gap analysis finds a coverage gap | `gap_description`, `gap_for` (tool_id with the gap) |
| `gap_candidate_found` | A complementary tool found to close a gap | `candidate`, `action: "curate_now" \| "queue"` |
| `tool_catalogued` | On approval | `tool_id`, `type: "mcp" \| "skill-pack" \| "agent-config"`, `vendor`, `verdict`, `crud_methods_classified` |
| `tool_rejected` | On rejection | `tool_id`, `reason` |

### Generic

| `event_type` | When emitted | Required payload |
|---|---|---|
| `warn` | Non-fatal anomaly | `message`, `context: {...}` |
| `error` | Fatal failure | `message`, `error: { name, message, stack }`, `recoverable: bool` |
| `human_gate` | Any human interaction point | `gate_name`, `presented`, `decision`, `modifications` |

---

## Emission mechanics

In a skill body, after generating `run_id` at invocation start:

```bash
LOG_FILE="$AMS_HOME/logs/learn-codebase-$(date -u +%Y-%m-%dT%H-%M-%S)-${RUN_ID}.jsonl"
mkdir -p "$AMS_HOME/logs"

emit_event() {
  local event_type="$1"
  local level="${2:-info}"
  local step="${3:-null}"
  local payload="${4:-{}}"
  jq -nc \
    --arg ts "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)" \
    --arg run "$RUN_ID" \
    --arg skill "learn-codebase" \
    --arg type "$event_type" \
    --arg lvl "$level" \
    --arg step "$step" \
    --argjson p "$payload" \
    '{timestamp: $ts, run_id: $run, skill: $skill, event_type: $type, level: $lvl, step: $step, payload: $p}' \
    >> "$LOG_FILE"
}

# Then at each event point:
emit_event "invocation_start" "info" "0" "$(jq -nc --arg t "$TARGET" '{target: $t, ams_version: "v2.1"}')"
```

Skills don't need to write the bash helper from scratch — they reference this
procedure for the schema and use a consistent helper. For Claude-driven skills,
each step in the skill body says **"emit `<event_type>` with payload {...}"**
and Claude composes the appropriate jq invocation.

---

## What logs unlock (debug-from-logs catalogue)

For each issue we hit in the smoke test, here's what the log would have shown:

| Issue | Log signal |
|---|---|
| `.git/info/exclude` not written | Missing `gitignore_update` event between `step_start: 11` and `step_end: 11` (or `step_start: 11` never appeared at all) |
| Claude-mem project-ID mismatch | `claude_mem_project_id_resolved` event with `auto_detected_id: "agent-management-studio/..."` and `target_basename: "aceik-sandpit-xmc"` mismatch — visible at start of run, not after the fact |
| Learn-codebase stalled at SDK | Last `step_end` event would pinpoint exactly which step finished; absence of subsequent `step_start` shows where execution died |
| Setup probe fail-soft | `dependency_probe` with `outcome: "unreachable"` followed by absence of `dependency_remediation` would show the soft-fail path was taken |
| SDK observation overload | Sequence of `claude_mem_observation_failed` events with increasing frequency would surface saturation pattern |
| Selective seeding | `cognitive_team_approved` with full payload shows exactly what the dev accepted |

Every issue in the v2.1 punch list becomes diagnostic-by-design rather than
forensic-after-the-fact.

---

## Retention

Logs accumulate. Retention policy for `logs/`:

- v2.1 default: keep last 50 runs per skill, prune older
- All-time logs are kept for the most recent 7 days regardless of count
- Pruning runs at the start of each `learn-codebase` invocation (cheap)
- Log files are JSONL — easy to grep, easy to import to any analysis tool

---

## Reading a log

Quick patterns:

```bash
# Last invocation_end and its outcome
tail -1 logs/learn-codebase-*.jsonl | jq 'select(.event_type=="invocation_end")'

# Find the step that stalled (no step_end after a step_start)
jq -c 'select(.event_type | startswith("step_"))' logs/<file>.jsonl | tail -10

# All errors across all runs
cat logs/*.jsonl | jq -c 'select(.level=="error")'

# Project-ID resolution decisions
cat logs/*.jsonl | jq -c 'select(.event_type=="claude_mem_project_id_resolved")'

# Did Step 11 (gitignore) run?
grep '"step":"11"' logs/<file>.jsonl
```

---

## Cross-referencing claude-mem's own logs

Claude-mem keeps its own operational log at:

```
$CLAUDE_MEM_DATA_DIR/logs/claude-mem-<YYYY-MM-DD>.log
```

(Default `CLAUDE_MEM_DATA_DIR` = `~/.claude-mem/` on Windows:
`C:\Users\<user>\.claude-mem\logs\claude-mem-<YYYY-MM-DD>.log`. Configurable
via `CLAUDE_MEM_DATA_DIR` env var.)

Format is **structured text, not JSONL**:

```
[2026-05-06 20:36:29.900] [INFO ] [DB    ] [session-1] STORED | sessionDbId=1 | obsCount=1 | obsIds=[147]
[2026-05-06 20:36:29.900] [INFO ] [CHROMA_SYNC] Syncing observation {observationId=147, project=<project>}
[2026-05-06 19:48:21.598] [WARN ] [SDK_SPAWN] [session-4] child emitted error event {...}
```

Use `grep` / `sed` / `awk` for parsing rather than `jq`.

### Why cross-reference

AMS logs capture **what we tried to do** to claude-mem. Claude-mem logs capture
**what claude-mem actually did**. Discrepancies are diagnostic gold.

| AMS log says | Claude-mem log should show | If absent / different → |
|---|---|---|
| `claude_mem_observation_seeded` at T with `project=aceik-sandpit-xmc` | `STORED` event at ~T with matching project tag | Project-ID misroute or write failed |
| `claude_mem_project_id_resolved` with `auto_detected_id: X` | A `[CHROMA_SYNC] Syncing observation` line with `project=X` | Confirms claude-mem's view matches what AMS thought |
| `dependency_probe: claude-mem unreachable` | Likely no log activity at that timestamp (worker dead) OR error chain | Distinguishes "worker dead" from "network blocked" |

### Useful claude-mem log queries

```bash
CMEM_LOG="$CLAUDE_MEM_DATA_DIR/logs/claude-mem-$(date -u +%Y-%m-%d).log"

# All observations stored in the last hour
grep "STORED" "$CMEM_LOG" | tail -20

# All errors and warnings since a known timestamp
awk '$1 >= "[2026-05-06" && $1 <= "[2026-05-06" && /\[WARN |\[ERROR/' "$CMEM_LOG"

# Project-tag history (cross-checks AMS's resolved project ID)
grep -oE "project=[^ ,}]+" "$CMEM_LOG" | sort -u

# SDK abort events (would show learn-codebase stalling cause)
grep "SDK_SPAWN" "$CMEM_LOG" | grep -E "abort|SIGTERM|SIGKILL"

# Per-session activity for a specific session ID
grep "session-4" "$CMEM_LOG" | tail -50

# Worker restarts (uptime resets)
grep "stale memory_session_id" "$CMEM_LOG"
```

### Other claude-mem artifacts worth knowing

`$CLAUDE_MEM_DATA_DIR/` also contains:

| Path | Purpose | Useful for |
|---|---|---|
| `claude-mem.db` | SQLite observation store | Direct query if HTTP API is down: `sqlite3 claude-mem.db 'SELECT id, project, type, title FROM observations ORDER BY id DESC LIMIT 20'` |
| `chroma/` | ChromaDB vector index | Semantic search backend; not directly queryable without claude-mem code |
| `observer-sessions/` | Per-session JSON state | If a session goes weird, inspect the corresponding session file |
| `worker.pid` | Current worker PID | Sanity-check the worker process is alive |
| `supervisor.json` | Worker supervisor state | Last-known worker config |
| `backups/` | DB backups | Recovery path if observation store gets corrupted |
| `chroma-sync-state.json` | Sync cursor between SQLite → Chroma | If observations are stored but not searchable, check this |

### How to surface claude-mem references in AMS logs

When an AMS skill needs to record a claude-mem interaction, the event payload
should include:

```json
{
  "claude_mem_log_file": "C:\\Users\\Local User\\.claude-mem\\logs\\claude-mem-2026-05-06.log",
  "claude_mem_log_grep_hint": "session-4",
  "claude_mem_db": "C:\\Users\\Local User\\.claude-mem\\claude-mem.db"
}
```

…so a debugger reading the AMS log can immediately know which file to grep
in claude-mem's data dir.

---

## Future: structured viewer

v3 may add a small `ams-log-view` CLI that prettyprints recent runs, filters
by event type, joins AMS-side and claude-mem-side logs by timestamp, and
produces summary tables. v2.1 is JSONL + jq + grep on claude-mem text logs —
sufficient for now.
