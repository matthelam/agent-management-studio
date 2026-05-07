# Audit Logging Service

The audit logging service is the single write path for all audit log entries. Every behaviour and command that generates an auditable event calls this service. No component writes audit log entries directly.

---

## Responsibilities

1. Accept a structured log entry conforming to `agency/audit/schema.md`
2. Validate that required envelope fields are present
3. Append the entry to the appropriate log file(s)
4. Never block the calling operation — logging failures are noted but do not halt execution

---

## Storage

### Two-Tier Model

All audit data is stored in two complementary tiers:

1. **Per-work-item logs** — the primary tier. Full event detail for every event in a work item.
2. **Category indexes** — the secondary tier. Small summary pointer files for cross-cutting queries.

There is no global audit log. Cross-work-item queries use the appropriate category index, then follow pointers to per-work-item logs for full detail.

### Work-Item Logs (Primary Tier)

Every work item has its own JSONL log file:

```
work-items/
  WORK-001.jsonl
  WORK-002.jsonl
  ...
```

All events with a non-null `work_item_id` are appended to the corresponding file. This is the primary log for investigation of a specific work item. Full event payloads live here.

### Category Indexes (Secondary Tier)

Eight purpose-built index files live under `agency/audit/indexes/`. Each contains summary pointer entries for one event category:

```
agency/audit/indexes/
  update-history.jsonl       ← one entry per /update session
  rescan-history.jsonl       ← one entry per /rescan session
  clarity-items.jsonl        ← one entry per clarity item identified
  delegations.jsonl          ← one entry per agent delegation decision
  reclassifications.jsonl    ← one entry per severity reclassification
  drift-detections.jsonl     ← one entry per drift flag at verification
  human-gates.jsonl          ← one entry per human gate decision
  backlog-activity.jsonl     ← one entry per backlog event (activation, fetch, transition, elaboration, completion check)
```

Index entries are summary pointers — not full payload copies. Each entry includes `work_item_id` and `session_id` references so the full event can be retrieved from the per-work-item log.

Entry schemas for each index file: `agency/audit/indexes/schemas.md`

### Session Index

Each session is recorded in an index file for fast lookup:

```
audit/
  sessions.jsonl
```

One entry per session:

```json
{
  "session_id": "SESSION-20260220-001",
  "started_at": "ISO-8601",
  "work_item_id": "WORK-001 | null",
  "command": "/work | /rescan | /update | /init",
  "actor": "human"
}
```

---

## Write Rules

### Append-Only

Log files are never modified after writing. Entries are always appended. No entry is ever deleted or overwritten.

### Ordering

Entries are written in the order events occur. The `timestamp` field is the authoritative ordering key for queries.

### Atomicity

Each JSONL line is written as a complete entry. Partial writes do not occur. If a write cannot complete, the failure is logged to a local error file (`agency/audit/errors.jsonl`) and execution continues.

### Encoding

All log files use UTF-8 encoding. All timestamps are ISO-8601 in UTC.

### Dual-Write Behaviour

Every event is written to **both** tiers when applicable:

| Condition | Writes to |
|-----------|-----------|
| Event has a non-null `work_item_id` | Per-work-item log (`work-items/WORK-NNN.jsonl`) |
| Event has a non-null `work_item_id` (always) | Per-work-item log |
| Event maps to a category index (see `agency/audit/schema.md`) | Category index file (`agency/audit/indexes/<category>.jsonl`) |
| Event is session-scoped (no `work_item_id`) | Category index file only |

The per-work-item log always gets the full event payload. The category index always gets a summary pointer entry.

---

## Service Interface

When a behaviour or command needs to log an event, it constructs the entry per `agency/audit/schema.md` and passes it to the logging service. The calling behaviour provides all payload fields; the service adds nothing to the payload.

The service is responsible for:
- Setting `timestamp` if not provided by the caller
- Writing to the per-work-item log (if `work_item_id` is set)
- Writing a summary pointer to the relevant category index (if the event type maps to an index — see `agency/audit/schema.md`)
- Handling write failures gracefully

### Call pattern

```
audit_log({
  type: "phase_transition",
  session_id: "SESSION-20260220-001",
  work_item_id: "WORK-001",
  actor: "system",
  payload: {
    from: "brief",
    to: "self_assess"
  }
})
```

---

## Log Rotation

Per-work-item logs are bounded by the size of a single work item's events and are never rotated.

Category index files are inherently bounded by event category frequency and never require rotation.

The `audit/sessions.jsonl` file grows indefinitely. If it exceeds 10,000 lines, rotate it:

```
audit/
  sessions.jsonl             ← current index
  sessions-2026-02.jsonl     ← rotated archive (YYYY-MM)
```

---

## Error Handling

If a write fails:

1. Append a record to `agency/audit/errors.jsonl`:

```json
{
  "timestamp": "ISO-8601",
  "failed_entry_type": "phase_transition",
  "work_item_id": "WORK-001",
  "error": "string describing failure"
}
```

2. Continue execution. The logging service never throws an exception that halts the calling behaviour.

3. At session end, if `agency/audit/errors.jsonl` contains entries from the current session, surface a warning to the human:

```
⚠ Audit log write failures occurred during this session. Some events may not be recorded. See agency/audit/errors.jsonl for details.
```

---

## References

- Entry schema: `agency/audit/schema.md`
- Index entry schemas: `agency/audit/indexes/schemas.md`
- Index directory layout: `agency/audit/indexes/README.md`
- Investigation queries: `agency/engines/investigation/procedures/investigation.md`
