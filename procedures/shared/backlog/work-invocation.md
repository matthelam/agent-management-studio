# Extended /work Invocation

Defines the extended invocation syntax for `/work` when backlog mode is ON.

---

## Invocation Formats

### Standard (always available)

```
/work <mode> "<brief description>"
```

Works identically whether backlog mode is ON or OFF. The manual brief text is used as-is.

### Direct Ticket Reference (backlog mode required)

```
/work <mode> <PROJ-NNN>
```

Examples:
```
/work fix SCRUM-314
/work change SCRUM-321
/work upgrade SCRUM-400
```

Fetches the Jira ticket and populates the brief from it. The mode provided in the command is used as a starting point — the issue type mapping may suggest a different mode, which the human confirms or overrides at the brief gate.

### Sprint Mode (backlog mode required)

```
/work <mode> sprint <N>
```

Examples:
```
/work fix sprint 7
/work change sprint 7
```

Enters autonomous sprint execution mode. The orchestration agent picks from the top of the sprint and works items sequentially until the sprint is empty or the human intervenes.

---

## Sprint Mode — Autonomous Execution Loop

When sprint mode is invoked, the orchestration agent enters an autonomous loop:

### Loop Procedure

```
1. Query sprint items:
   JQL: sprint = <N> AND status = 'To Do' ORDER BY rank ASC

2. If no items remain → report "Sprint <N> complete. All items Done." → exit loop

3. Pick the top-ranked item (index 0)

4. Execute the full 5-phase workflow on the picked item:
   Brief → Self-Assess → Plan → Execute → Final Verify
   (all human gates apply per the standard workflow)

5. On completion → run completion check (transition ticket to Done)

6. Return to step 1 (re-query to get fresh sprint state)
```

### Key Rules

- **No selection menu.** The agent picks from the top of the sprint — it does not present options to the human.
- **All human gates still apply.** Sprint mode does not bypass Brief, Plan, or Final Verify gates. The human pre-approves gates per their instruction, but the gates are still structurally present.
- **Fresh query each iteration.** After completing each item, re-query the sprint. Items may have been added, removed, or reordered externally.
- **Mode from invocation applies to all items.** If `/work fix sprint 7` was invoked, all items are worked in Fix mode. If the issue type mapping suggests a different mode for a specific ticket, the brief gate provides the opportunity to override.

### Human Intervention

The human can intervene at any point during the sprint loop:

| Intervention | Effect |
|-------------|--------|
| Reject a brief gate | Agent skips that item, logs the rejection, picks the next item |
| Reject a plan gate | Agent returns to planning for that item (standard flow) |
| Reject a final verify gate | Agent returns to execution for that item (standard flow) |
| "Stop" or "pause" | Agent exits the sprint loop, reports progress |

### Sprint Mode Reporting

After each completed item, report a brief status:

```
✓ SCRUM-314 — Done (1 of N sprint items)
  Picking next: SCRUM-321...
```

On sprint completion:

```
Sprint 7 complete.
  Items worked: 5
  Items completed: 4
  Items skipped (rejected at brief): 1
```

---

## Argument Parsing

The backlog mode check in `work.md` determines the invocation type:

| Argument Pattern | Detection | Flow |
|-----------------|-----------|------|
| Quoted string: `"..."` | Starts and ends with `"` | Manual brief (standard) |
| Ticket key: `PROJ-NNN` | Matches regex `^[A-Z]+-\d+$` | Direct ticket reference |
| Sprint: `sprint N` | Starts with `sprint` followed by a number | Sprint mode |
| Bare text without quotes | Does not match ticket or sprint pattern | Manual brief (standard) |

If backlog mode is OFF and a ticket key or sprint argument is provided:

```
⚠ Backlog mode is not active. Use /connect <path> --jira to enable Jira integration.
Proceeding with "<argument>" as a manual brief.
```

---

## Audit Logging

Sprint mode logs a `preflight_check` at the start of the loop:

```json
{
  "type": "preflight_check",
  "actor": "system",
  "payload": {
    "check": "sprint_mode_entry",
    "sprint_id": 7,
    "items_in_sprint": 12,
    "items_todo": 8
  }
}
```

Each individual ticket worked within the sprint loop generates its own full audit trail (all standard work item events).
