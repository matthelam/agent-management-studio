# Index Entry Schemas

Summary pointer schemas for each category index file. All entries include `session_id` and either `work_item_id` or `null` for session-scoped events. Full event detail is always in the work-item log.

---

## update-history.jsonl

One entry per `/update` session. Written when `update_completed` fires.

```json
{
  "session_id": "SESSION-20260220-001",
  "work_item_id": null,
  "timestamp": "ISO-8601",
  "changes_detected": 5,
  "changes_applied": 3,
  "changes_deferred": 1,
  "changes_skipped": 1,
  "agents_updated": ["frontend-dev", "code-review"],
  "snapshot_updated_to": "ISO-8601"
}
```

---

## rescan-history.jsonl

One entry per `/rescan` session. Written when `rescan_result` fires.

```json
{
  "session_id": "SESSION-20260220-002",
  "work_item_id": null,
  "timestamp": "ISO-8601",
  "flags": ["--full"],
  "changes_detected": 3,
  "by_impact": {
    "major": 1,
    "medium": 1,
    "minor": 1
  }
}
```

---

## clarity-items.jsonl

One entry per clarity item identified. Written when `clarity_item` fires.

```json
{
  "session_id": "SESSION-20260220-003",
  "work_item_id": "WORK-001",
  "timestamp": "ISO-8601",
  "item_id": "clarity-001",
  "sub_directive": "done-state | decision-authority | assumption-risk",
  "item_type": "gap | assumption",
  "severity": "critical | medium | low",
  "description": "string"
}
```

---

## delegations.jsonl

One entry per agent delegation decision. Written when `clarity_resolution` fires with `action = "delegated"` or `action = "bulk_delegated"`.

```json
{
  "session_id": "SESSION-20260220-003",
  "work_item_id": "WORK-001",
  "timestamp": "ISO-8601",
  "item_id": "clarity-002",
  "delegated_to": "agent:frontend-dev",
  "original_severity": "medium",
  "decision": "string"
}
```

---

## reclassifications.jsonl

One entry per severity reclassification. Written when `clarity_resolution` fires with `action = "reclassified"`.

```json
{
  "session_id": "SESSION-20260220-003",
  "work_item_id": "WORK-001",
  "timestamp": "ISO-8601",
  "item_id": "clarity-003",
  "original_severity": "critical",
  "new_severity": "medium",
  "reclassified_by": "human",
  "reasoning": "string"
}
```

---

## drift-detections.jsonl

One entry per drift flag at verification. Written when `verification_result` fires with `drift_detected = true`.

```json
{
  "session_id": "SESSION-20260220-004",
  "work_item_id": "WORK-001",
  "timestamp": "ISO-8601",
  "ac_index": 2,
  "ac_text": "string",
  "clarity_item_id": "clarity-001",
  "evidence": "string"
}
```

---

## human-gates.jsonl

One entry per human gate decision. Written when `human_gate` fires.

```json
{
  "session_id": "SESSION-20260220-003",
  "work_item_id": "WORK-001",
  "timestamp": "ISO-8601",
  "gate": "after_brief | after_plan | after_final_verify",
  "decision": "approved | rejected | modified",
  "ticket_key": "SCRUM-314 | null"
}
```

`ticket_key` is populated when backlog mode is ON and the work item has a Jira ticket reference. `null` otherwise. This enables cross-referencing human gate decisions with backlog activity.

---

## backlog-activity.jsonl

One entry per backlog-related event. Written when any `backlog_*` event type fires.

```json
{
  "session_id": "SESSION-20260220-005",
  "work_item_id": "WORK-001 | null",
  "timestamp": "ISO-8601",
  "event_type": "backlog_mode_activated | backlog_ticket_fetched | backlog_transition | backlog_elaboration | backlog_completion_check",
  "ticket_key": "SCRUM-314 | null",
  "outcome": "string"
}
```

`ticket_key` is populated for ticket-scoped events. `null` for `backlog_mode_activated` and `backlog_elaboration`. `outcome` is a short summary (e.g. `"success"`, `"failed"`, `"auto_selected"`).
