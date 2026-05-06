# Ticket Lifecycle Management

Maps work item phases to Jira status transitions. Keeps the Jira ticket in sync with the delivery workflow.

---

## When This Behaviour Applies

This behaviour activates when ALL of these conditions are met:

1. Backlog mode is ON
2. The work item has a `backlog.ticket_key` (was populated from a Jira ticket)
3. A phase transition or human gate occurs

If the work item was created with a manual brief (no ticket reference), this behaviour does NOT activate — even when backlog mode is ON.

---

## Phase-to-Transition Mapping

| Work Event | Jira Action | Trigger Point |
|------------|-------------|---------------|
| Brief entry (ticket fetched) | Transition to "In Progress" | After successful ticket fetch in Phase 1 |
| Plan approved (Gate 2) | Add comment with plan summary | After human approves the execution plan |
| Execute started | No transition (already "In Progress") | — |
| Final Verify pass + Gate 3 approved | Transition to "Done" + closing comment | After human accepts delivery |

---

## Transition Rules

### Always Resolve Dynamically

Before attempting any transition, call `getTransitionsForJiraIssue(cloudId, issueKey)` to discover available transitions. **Never hardcode transition IDs.** Jira workflows vary between projects and boards.

### Match by Target Status Name

Find the transition whose target status matches the desired state:

- For "In Progress": look for a transition whose `to.name` contains "In Progress" or "In Development"
- For "Done": look for a transition whose `to.name` contains "Done" or "Closed" or "Resolved"

Use case-insensitive partial matching. If multiple transitions match, prefer the one with the shortest name (most likely the default).

### Handle Unavailable Transitions

If no matching transition is available:

1. Log a warning with the available transitions
2. Warn the human: "Cannot transition `<ticket_key>` to `<target_status>`. Available transitions: `<list>`. Manual transition may be required."
3. Continue execution — do not block the work item on a failed transition

### Handle Already-In-Target-State

If the ticket is already in the target status:

1. Skip the transition silently
2. Log the skip with `outcome: "skipped"` in the audit event

---

## Comment Templates

### Plan Approved Comment

Added after Gate 2 (plan approval):

```
🤖 **Agent Plan Approved**

**Work Item:** {work_item_id}
**Mode:** {mode}
**Lead Agent:** {lead_agent}

**Approach:**
{plan_summary}

**Files to modify:**
{file_list}

**Test strategy:**
{test_strategy}
```

### Closing Comment

Added after Gate 3 (final verify acceptance):

```
🤖 **Work Complete**

**Work Item:** {work_item_id}
**Mode:** {mode}
**Status:** All acceptance criteria verified

**Summary of changes:**
{change_summary}

**Verification:**
{verification_summary}
```

---

## Audit Logging

Every transition attempt is logged via the audit logging service (`agency/audit/service.md`):

```json
{
  "type": "backlog_transition",
  "session_id": "SESSION-...",
  "work_item_id": "WORK-001",
  "actor": "system",
  "payload": {
    "ticket_key": "SCRUM-314",
    "from_status": "To Do",
    "to_status": "In Progress",
    "transition_id": "21",
    "trigger": "brief_entry",
    "outcome": "success",
    "failure_reason": null
  }
}
```

Comments added to tickets are NOT separately logged — they are informational supplements to the transitions.

---

## Error Recovery

| Scenario | Handling |
|----------|----------|
| Jira API timeout | Retry once. On second failure, log and continue. |
| Ticket not found (deleted externally) | Warn human, detach backlog reference, continue as manual work item. |
| Permission denied | Warn human, log, continue. |
| Transition conflict (e.g. ticket moved externally) | Re-fetch ticket status, log the mismatch, warn human. |

The lifecycle behaviour is advisory, not blocking. A failed Jira interaction never halts the delivery workflow. The completion check (`completion-check.md`) provides the safety net.
