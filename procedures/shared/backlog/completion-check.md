# Completion Check — Never Leave a Ticket Behind

Runs after the Final Verify human gate, before marking the work item as `done`. Ensures the Jira ticket is in the correct terminal state.

---

## When This Behaviour Runs

This behaviour runs when ALL of these conditions are met:

1. Backlog mode is ON
2. The work item has a `backlog.ticket_key`
3. The human has approved the Final Verify gate (Gate 3)
4. The work item is about to transition to `done`

---

## Procedure

### Step 1 — Re-fetch Ticket State

Call `getJiraIssue(cloudId, ticketKey)` to get the current Jira ticket status.

This is a fresh fetch — do not rely on cached state. The ticket may have been moved externally between the start of work and the final verify.

### Step 2 — Evaluate Current State

| Current Status | Action |
|----------------|--------|
| Already "Done" (or equivalent terminal state) | Skip transition. Log `action_taken: "already_done"`. |
| "In Progress" or any non-terminal state | Attempt transition to "Done". |
| Ticket not found (deleted externally) | Log warning. Detach backlog reference. Continue to mark work item as `done`. |

### Step 3 — Attempt Transition

If the ticket is not in a terminal state:

1. Call `getTransitionsForJiraIssue(cloudId, ticketKey)` to discover available transitions
2. Find a transition whose target status matches "Done" (see matching rules in `lifecycle.md`)
3. Call `transitionJiraIssue(cloudId, ticketKey, transitionId)`

### Step 4 — Add Closing Comment

Regardless of transition outcome, add a closing comment to the ticket using the template from `lifecycle.md`.

### Step 5 — Handle Failures

If the transition fails:

1. Log the failure with `action_taken: "failed"` and the failure reason
2. Present to the human:

```
⚠ Could not transition <ticket_key> to Done.
Current status: <actual_status>
Available transitions: <list>

The work item has been verified and accepted. Please transition the ticket manually.
```

3. If the human cannot resolve it immediately, log `action_taken: "escalated_to_human"` and proceed to mark the work item as `done`

The completion check never blocks the work item from completing. The work is done — only the Jira state needs reconciliation.

---

## Audit Logging

Via audit logging service (`agency/audit/service.md`):

```json
{
  "type": "backlog_completion_check",
  "session_id": "SESSION-...",
  "work_item_id": "WORK-001",
  "actor": "system",
  "payload": {
    "ticket_key": "SCRUM-314",
    "expected_status": "Done",
    "actual_status": "In Progress",
    "action_taken": "transitioned | already_done | failed | escalated_to_human",
    "closing_comment_added": true
  }
}
```

---

## Parent Ticket Rollup

When the completed ticket is a subtask, check if all sibling subtasks under the same parent are now "Done":

1. Fetch the parent issue
2. Fetch all subtasks of the parent
3. If ALL subtasks are "Done" → attempt to transition the parent to "Done" (same dynamic resolution rules)
4. If NOT all subtasks are done → add an informational comment to the parent noting the completed subtask

This cascading completion only goes up one level. It does not recursively check grandparents.
