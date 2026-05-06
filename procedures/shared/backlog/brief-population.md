# Brief Population from Jira Tickets

Populates a work item brief from a Jira ticket when backlog mode is ON and a ticket reference is provided.

---

## When This Behaviour Applies

This behaviour activates during Phase 1 (Brief) when ALL of these conditions are met:

1. Backlog mode is ON (`.claude/state.json` contains a `jira` block)
2. The `/work` invocation includes a ticket reference (e.g. `SCRUM-314`) or a sprint reference (e.g. `sprint 7`)
3. The ticket exists and is accessible in the configured Jira project

If the `/work` invocation provides a manual brief string (e.g. `/work fix "Fix the login bug"`), this behaviour does NOT activate — even when backlog mode is ON. The manual brief is used as-is and the standard clarity assessment proceeds.

---

## Ticket Fetch

### Direct Reference

When the brief matches a Jira ticket key pattern (`PROJ-NNN`):

1. Call `getJiraIssue(cloudId, issueKey)` to fetch the ticket
2. If the ticket does not exist or is not accessible → error: "Ticket `<key>` not found or not accessible in project `<project_key>`."
3. Proceed to field mapping

### Sprint Pick

When the invocation is `/work <mode> sprint <N>`:

1. Call `searchJiraIssuesUsingJql` with: `sprint = <N> AND status = 'To Do' ORDER BY rank ASC`
2. Pick the top-ranked item automatically — do NOT present a selection menu
3. If the sprint has no remaining 'To Do' items → report: "Sprint `<N>` has no remaining items in 'To Do' status."
4. Proceed to field mapping with the picked ticket

---

## Field Mapping

| Jira Field | Maps To | Notes |
|------------|---------|-------|
| `summary` | work item `brief` | Used as the primary brief text |
| `description` | context + acceptance criteria | Parse structured ACs if present (e.g. bullet lists under "Acceptance Criteria" heading). Otherwise treat as supplementary context. |
| `priority` | `urgency` | See priority-to-urgency mapping in `schemas.md` |
| `issuetype` | mode hint | See issue type-to-mode hint in `schemas.md`. Present as suggestion — human confirms or overrides during the brief gate. |
| `labels` | tags (informational) | Included in the brief for context |
| `parent` | parent context | If the ticket is a subtask, fetch parent summary for context |

### Acceptance Criteria Extraction

Scan the Jira description for structured acceptance criteria. Look for:

- Markdown checkbox lists (`- [ ] criterion`)
- Numbered lists under an "Acceptance Criteria" heading
- Bullet lists under an "AC" or "Acceptance Criteria" section

If structured ACs are found, populate the work item `acceptance_criteria` array directly. If no structured ACs are found, the standard clarity assessment will identify gaps (this is the normal flow — the clarity assessment is designed to handle incomplete briefs).

---

## Work Item Record

The populated work item record includes the Jira ticket reference:

```json
{
  "id": "WORK-001",
  "brief": "<ticket summary>",
  "mode": "fix | change | upgrade",
  "urgency": "normal | elevated | critical",
  "acceptance_criteria": ["<extracted or empty>"],
  "agents": [],
  "status": "brief",
  "backlog": {
    "ticket_key": "SCRUM-314",
    "ticket_id": "10789",
    "source": "direct_reference | sprint_pick",
    "sprint_id": "7 | null"
  },
  "phases": {},
  "log": "work-items/WORK-001.jsonl"
}
```

---

## Audit Logging

Via audit logging service (`agency/audit/service.md`):

```json
{
  "type": "backlog_ticket_fetched",
  "session_id": "SESSION-...",
  "work_item_id": "WORK-001",
  "actor": "system",
  "payload": {
    "ticket_key": "SCRUM-314",
    "ticket_summary": "Fix login validation",
    "ticket_type": "Bug",
    "ticket_priority": "High",
    "mode_hint": "fix",
    "urgency_mapped": "elevated",
    "source": "direct_reference",
    "sprint_id": null
  }
}
```

---

## What Happens Next

After brief population, the standard Phase 1 flow continues unchanged:

1. The clarity assessment runs on the populated brief (agents evaluate Done State, Decision Authority, Assumption Risk)
2. The human gate after brief presents the ticket-populated brief for approval
3. The human can modify the mode, urgency, or acceptance criteria

The brief population behaviour only provides the starting data — it does not bypass any existing quality gates.
