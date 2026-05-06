# Audit Log Entry Schema

All audit log entries are written as JSONL (one JSON object per line). Every entry shares a common envelope; the `payload` field is type-specific.

Every event is written to the per-work-item log (`work-items/WORK-NNN.jsonl`) when `work_item_id` is non-null. Specific event types also write a summary pointer to a category index file — these are noted per event type below.

---

## Common Envelope

```json
{
  "type": "string",
  "timestamp": "ISO-8601",
  "session_id": "string",
  "work_item_id": "string | null",
  "actor": "human | agent:<agent-name> | system",
  "payload": {}
}
```

| Field | Description |
|-------|-------------|
| `type` | Event type. One of the defined types below. |
| `timestamp` | ISO-8601 UTC timestamp of the event. |
| `session_id` | Unique identifier for the current session (e.g. `SESSION-20260220-001`). Groups all events from a single invocation. |
| `work_item_id` | ID of the work item in scope (e.g. `WORK-001`). `null` for events outside a `/work` session (e.g. `/rescan`, `/update`). |
| `actor` | Who caused the event. `human` for human-initiated actions. `agent:<name>` for agent actions (e.g. `agent:frontend-dev`). `system` for automated system events. |
| `payload` | Type-specific fields. Defined per event type below. |

---

## Event Types

### `phase_transition`

A work item moved from one workflow phase to another.

> **Index:** none — per-work-item log only.

```json
{
  "type": "phase_transition",
  "payload": {
    "from": "brief | self_assess | plan | execute | final_verify | null",
    "to": "brief | self_assess | plan | execute | final_verify | done"
  }
}
```

`from` is `null` when the work item is first created.

---

### `preflight_check`

The environment freshness check at `/work` start.

> **Index:** none — per-work-item log only.

```json
{
  "type": "preflight_check",
  "payload": {
    "check": "environment_freshness",
    "snapshot_age_days": 12,
    "threshold_days": 7,
    "snapshot_timestamp": "ISO-8601",
    "outcome": "fresh | stale | missing",
    "human_decision": "proceed | update | null"
  }
}
```

`human_decision` is `null` when outcome is `fresh` (no challenge presented).

---

### `clarity_assessment_initiated`

A Clarity Assessment began for a work item.

> **Index:** none — per-work-item log only.

```json
{
  "type": "clarity_assessment_initiated",
  "payload": {
    "agents": ["frontend-dev", "backend-dev"],
    "brief_length_chars": 342
  }
}
```

---

### `clarity_item`

A single gap or assumption identified during Clarity Assessment.

> **Index:** `audit/indexes/clarity-items.jsonl` — one summary pointer per item.

```json
{
  "type": "clarity_item",
  "payload": {
    "item_id": "clarity-001",
    "sub_directive": "done-state | decision-authority | assumption-risk",
    "item_type": "gap | assumption",
    "severity": "critical | medium | low",
    "description": "string"
  }
}
```

One entry per item identified. Logged at assessment time before any resolution.

---

### `clarity_resolution`

A single Clarity Assessment item was resolved.

> **Index:** `audit/indexes/delegations.jsonl` when `action = "delegated"` or `"bulk_delegated"`.
> **Index:** `audit/indexes/reclassifications.jsonl` when `action = "reclassified"`.
> Other actions: per-work-item log only.

```json
{
  "type": "clarity_resolution",
  "payload": {
    "item_id": "clarity-001",
    "resolution_round": 1,
    "action": "resolved | delegated | reclassified | bulk_delegated",
    "resolved_by": "human | agent:<name>",
    "original_severity": "critical | medium | low",
    "new_severity": "critical | medium | low | null",
    "decision": "string",
    "reasoning": "string | null"
  }
}
```

`new_severity` is non-null only when `action` is `reclassified`. `reasoning` is populated for agent-delegated items.

---

### `clarity_report_final`

The Clarity Assessment completed and the final report was produced.

> **Index:** none — per-work-item log only.

```json
{
  "type": "clarity_report_final",
  "payload": {
    "agents": ["frontend-dev", "backend-dev"],
    "resolution_rounds": 2,
    "summary": {
      "critical": { "identified": 2, "resolved": 2 },
      "medium": { "identified": 3, "resolved": 3 },
      "low": { "identified": 1, "resolved": 1 }
    },
    "outcome": "ready | blocked"
  }
}
```

`outcome` is `ready` when zero Critical items remain. `blocked` should not occur in normal flow (agents do not proceed while Critical items are unresolved).

---

### `self_assessment`

An agent declared its involvement for a work item.

> **Index:** none — per-work-item log only.

```json
{
  "type": "self_assessment",
  "payload": {
    "declaration": "lead | support | observe",
    "reasoning": "string"
  }
}
```

One entry per agent per work item. `actor` identifies which agent.

---

### `resolver_decision`

The resolver processed an uncertainty during execution.

> **Index:** none — per-work-item log only.

```json
{
  "type": "resolver_decision",
  "payload": {
    "phase": "execute | plan | final_verify",
    "tier": "self_resolve | peer_consult | human_gate",
    "confidence": 0.55,
    "threshold": 0.60,
    "source": "clarity_report | live_assessment",
    "peer": "agent:<name> | null",
    "question": "string",
    "decision": "string",
    "reasoning": "string"
  }
}
```

`source` is `clarity_report` when the resolution was applied directly from a prior Clarity Assessment item. `peer` is non-null only for `peer_consult` tier.

---

### `human_gate`

A human gate was presented and the human responded.

> **Index:** `audit/indexes/human-gates.jsonl` — one summary pointer per gate.

```json
{
  "type": "human_gate",
  "payload": {
    "gate": "after_brief | after_plan | after_final_verify",
    "presented": ["string"],
    "decision": "approved | rejected | modified",
    "modifications": "string | null",
    "backlog_context": {
      "ticket_key": "SCRUM-314 | null",
      "ticket_status": "In Progress | null",
      "jira_comment_added": true,
      "jira_transition_triggered": "In Progress | Done | null"
    }
  }
}
```

`presented` lists the items shown to the human. `modifications` captures any changes the human made before approving. `backlog_context` is present only when backlog mode is ON and the work item has a ticket reference — otherwise the field is omitted entirely.

---

### `verification_result`

A single acceptance criterion was verified.

> **Index:** `audit/indexes/drift-detections.jsonl` when `drift_detected = true`.
> Other results: per-work-item log only.

```json
{
  "type": "verification_result",
  "payload": {
    "ac_index": 1,
    "ac_text": "string",
    "clarity_item_id": "clarity-001 | null",
    "status": "pass | fail",
    "evidence": "string",
    "drift_detected": false
  }
}
```

`clarity_item_id` links to the Clarity Report item that produced this AC, if applicable. `drift_detected` is `true` if the implementation deviated from a Clarity Report resolution.

---

### `rescan_initiated`

A `/rescan` command was invoked.

> **Index:** none — per-work-item log only (work_item_id is null for rescan sessions; see `rescan_result` for the index write).

```json
{
  "type": "rescan_initiated",
  "payload": {
    "flags": ["--full | --deps | none"],
    "baseline_timestamp": "ISO-8601 | null"
  }
}
```

`baseline_timestamp` is `null` if no snapshot exists.

---

### `rescan_result`

The `/rescan` diff result.

> **Index:** `audit/indexes/rescan-history.jsonl` — one summary pointer per rescan session.

```json
{
  "type": "rescan_result",
  "payload": {
    "changes_detected": 3,
    "by_impact": {
      "major": 1,
      "medium": 1,
      "minor": 1
    },
    "changes": [
      {
        "key": "frameworks/react",
        "from": "18.2.0",
        "to": "19.0.0",
        "impact": "major"
      }
    ]
  }
}
```

---

### `update_initiated`

A `/update` command was invoked.

> **Index:** none — per-session only (see `update_completed` for the index write).

```json
{
  "type": "update_initiated",
  "payload": {
    "flags": ["--auto | none"],
    "deferred_changes_re_surfaced": 1
  }
}
```

---

### `update_decision`

The human made a review decision on a single proposed change during `/update`.

> **Index:** none — per-session only.

```json
{
  "type": "update_decision",
  "payload": {
    "key": "frameworks/react",
    "change": "18.2.0 → 19.0.0",
    "impact": "major",
    "affected_agents": ["frontend-dev", "code-review"],
    "action": "approved | modified | skipped | deferred | auto_approved",
    "modification": "string | null",
    "defer_reason": "string | null"
  }
}
```

---

### `update_applied`

A single approved change was applied to an agent profile.

> **Index:** none — per-session only.

```json
{
  "type": "update_applied",
  "payload": {
    "key": "frameworks/react",
    "change": "18.2.0 → 19.0.0",
    "agent": "frontend-dev",
    "sections_modified": ["specialist_knowledge", "standards"]
  }
}
```

One entry per agent per change applied.

---

### `update_completed`

The `/update` command finished.

> **Index:** `audit/indexes/update-history.jsonl` — one summary pointer per update session.

```json
{
  "type": "update_completed",
  "payload": {
    "changes_detected": 5,
    "changes_applied": 3,
    "changes_deferred": 1,
    "changes_skipped": 1,
    "auto_applied": 1,
    "agents_updated": ["frontend-dev", "code-review"],
    "snapshot_updated_to": "ISO-8601"
  }
}
```

---

### `backlog_mode_activated`

Backlog mode was activated via `/connect --jira`.

> **Index:** `audit/indexes/backlog-activity.jsonl` — one summary pointer per activation.

```json
{
  "type": "backlog_mode_activated",
  "payload": {
    "cloud_id": "uuid",
    "project_key": "SCRUM",
    "site_name": "string",
    "discovery": "auto_selected | human_selected"
  }
}
```

`discovery` is `auto_selected` when only one site/project was available. `human_selected` when the human chose from multiple options.

---

### `backlog_ticket_fetched`

A Jira ticket was fetched to populate a work item brief.

> **Index:** `audit/indexes/backlog-activity.jsonl` — one summary pointer per fetch.

```json
{
  "type": "backlog_ticket_fetched",
  "payload": {
    "ticket_key": "SCRUM-314",
    "ticket_summary": "string",
    "ticket_type": "Bug | Story | Task | Epic",
    "ticket_priority": "Blocker | High | Medium | Low | Lowest",
    "mode_hint": "fix | change | upgrade",
    "urgency_mapped": "normal | elevated | critical",
    "source": "direct_reference | sprint_pick",
    "sprint_id": "number | null"
  }
}
```

`source` is `direct_reference` when the user provided a ticket key. `sprint_pick` when the orchestration agent picked from the top of a sprint.

---

### `backlog_transition`

A Jira status transition was attempted on a ticket.

> **Index:** `audit/indexes/backlog-activity.jsonl` — one summary pointer per transition attempt.

```json
{
  "type": "backlog_transition",
  "payload": {
    "ticket_key": "SCRUM-314",
    "from_status": "string",
    "to_status": "string",
    "transition_id": "string",
    "trigger": "brief_entry | plan_approved | final_verify_pass",
    "outcome": "success | failed | skipped",
    "failure_reason": "string | null"
  }
}
```

`outcome` is `skipped` when the ticket was already in the target state.

---

### `backlog_elaboration`

An elaboration produced an instruction plan and created issues in Jira.

> **Index:** `audit/indexes/backlog-activity.jsonl` — one summary pointer per elaboration.

```json
{
  "type": "backlog_elaboration",
  "payload": {
    "epics_created": 3,
    "stories_created": 10,
    "subtasks_created": 25,
    "dependencies_linked": 8,
    "jira_keys": {
      "epics": ["SCRUM-100", "SCRUM-101", "SCRUM-102"],
      "stories": ["SCRUM-103"],
      "subtasks": ["SCRUM-110"]
    }
  }
}
```

`jira_keys` lists are abbreviated in the index pointer. Full lists are in the work-item log.

---

### `backlog_completion_check`

The "never leave a ticket behind" check ran after Final Verify.

> **Index:** `audit/indexes/backlog-activity.jsonl` — one summary pointer per check.

```json
{
  "type": "backlog_completion_check",
  "payload": {
    "ticket_key": "SCRUM-314",
    "expected_status": "Done",
    "actual_status": "In Progress",
    "action_taken": "transitioned | already_done | failed | escalated_to_human",
    "closing_comment_added": true
  }
}
```

`action_taken` is `escalated_to_human` when the transition failed and the human was notified.
