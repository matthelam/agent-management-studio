# audit-logging Procedure

Cross-cutting concern: how every seeded skill emits structured events into the
two-tier audit log. Inlined as a reference into each skill's body so emissions
are consistent.

The audit harness itself (service definition + event schema + per-event index
discipline) lives in `audit/service.md` and `audit/schema.md`, both seeded into
target's `.claude/audit/`.

---

## When to emit

Every skill emits events at:
- **Phase boundaries** — `phase_transition` from previous to next
- **Decision points** — `resolver_decision`, `human_gate`, `update_decision`
- **External effects** — `commit_executed`, `jira_status_transition`,
  `ai_marker_stripped`
- **Findings & verifications** — `verification_result`, `findings_recorded`
- **Skill invocations & completions** — `<skill>_initiated`, `<skill>_completed`

The full event taxonomy is in `audit/schema.md`. Skills must use only schema'd
event types; introducing a new event requires updating the schema first.

---

## How to emit

The audit service exposes a single append-only operation. Skills invoke it via
the seeded service definition:

```
write_event({
  type: "<event_type>",
  actor: "human" | "system" | "agent:<name>",
  work_item_id: "<ticket-or-AMS-ref>" | null,
  session_id: "<auto>",
  timestamp: "<auto: ISO-8601>",
  payload: { ... }
})
```

The service:
1. Generates `session_id` (per Claude Code session) and `timestamp` if not
   provided.
2. Appends to the per-work-item log: `work-items/<work_item_id>.jsonl` (if
   `work_item_id` is set).
3. For events that should also write to category indexes (per
   `audit/schema.md`), appends a summary pointer to the relevant
   `audit/indexes/<category>.jsonl`.
4. On write failure: appends to `audit/errors.jsonl`. Failures must not block
   skill execution.

---

## The two-tier model

### Tier 1 — Per-work-item logs (full payload)

Path: `work-items/<work_item_id>.jsonl`

One JSONL line per event. Full payload. Source of truth for reconstructing a
work item's complete decision chain.

### Tier 2 — Category indexes (fast cross-cutting lookup)

Paths under `audit/indexes/`:

- `update-history.jsonl` — one entry per `update` skill session
- `clarity-items.jsonl` — one entry per clarity item identified
- `delegations.jsonl` — one entry per agent delegation decision
- `reclassifications.jsonl` — one entry per severity reclassification
- `drift-detections.jsonl` — one entry per drift flag at verification
- `human-gates.jsonl` — one entry per human gate decision

Index entries are **summary pointers**: `{event_type, work_item_id, timestamp,
summary_fields...}`. Querying for a full payload requires following the
`work_item_id` pointer to the per-work-item log.

There is no global `audit.jsonl`. Cross-work-item queries always use category
indexes.

---

## Skill-by-skill emission summary

| Skill | Key events emitted |
|---|---|
| `learn-codebase` | `learn_codebase_initiated`, `stack_detected`, `specialists_proposed`, `human_gate` (after specialist proposal), `learn_codebase_completed` |
| `update` | `update_initiated`, `behavioural_query`, `update_decision` (per change), `update_applied` (per agent per change), `update_completed` |
| `deliver-work` | `phase_transition` (×6), `preflight_check`, `clarity_assessment_initiated`, `clarity_item` (×n), `clarity_resolution`, `clarity_report_final`, `human_gate` (×3), `self_assessment` (per agent), `resolver_decision`, `verification_result` (per AC) |
| `audit-work` | `audit_initiated`, `perspective_changed`, `findings_recorded`, `audit_completed` |
| `finding` | `finding_created`, `finding_routed`, `finding_status_change` |
| `define-specialist` | `specialist_added`, `specialist_modified`, `specialist_promoted` |
| `commit-clean` | `commit_clean_invoked`, `ai_marker_stripped`, `commit_executed` |
| `jira-context` | `jira_context_invoked`, `jira_ticket_loaded`, `jira_status_transition`, `jira_completion_check` |
| Tool-safety (PreToolUse hook) | `prescriptive_rules_block` (when a hard-block fires) |

---

## Querying the audit log

The `audit-work` skill is the canonical reader of the audit log. It uses the
query patterns documented in (legacy) OLD investigation/procedures/investigation.md
(now folded into `audit-work.md`'s analysis step). Common queries:

- Reconstruct a full work-item decision chain — read the per-work-item log
- Find all human gate decisions — read `audit/indexes/human-gates.jsonl`
- Find all Critical clarity items + resolutions — read
  `audit/indexes/clarity-items.jsonl` filtered by severity, then follow
  `work_item_id` to the per-work-item log

See `audit-work.md` Step 3 (Evidence gathering) for the canonical query
patterns.

---

## Failure handling

The audit service is best-effort. If write fails:

1. Append failure to `audit/errors.jsonl` (location, intended event,
   error message).
2. Do not block the skill — return success to the caller.
3. Surface a non-fatal warning to the dev: *"Audit log write failed. Check
   `audit/errors.jsonl` for details. Skill continues."*

This is intentional — losing an audit event is preferable to losing the
work-in-progress because of an audit failure.
