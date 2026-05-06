# jira-context Procedure

Sub-skill of `deliver-work`. Triggered by natural language referencing
Jira/Atlassian or a Jira-formatted ticket ID (e.g. `SCRUM-374`,
`PROJ-1234`). Loads ticket context for the active work session.

Replaces (and tightens) the OLD `/connect --jira` discovery flow. The
project-resolution role of OLD `/connect` is obsolete in the seed-and-run
architecture (cwd is the source of truth); only the Jira-specific runtime
context-fetching behaviour migrates here.

---

## Step 1 — Verify Atlassian MCP

Check that the Atlassian MCP is registered in the active Claude Code session:

```bash
# pseudo: list available MCP tools
# look for: mcp__atlassian__getJiraIssue or similar
```

If the MCP is **not** available:

1. Surface install instructions:
   *"The Atlassian MCP isn't installed. To fetch Jira tickets directly, run:
   `/plugin marketplace add anthropics/claude-code-marketplace` then
   `/plugin install atlassian` (or follow the Atlassian MCP docs for your
   setup). Continue without Jira context for this session?"*
2. On dev confirmation: continue without Jira; deliver-work proceeds with
   manual brief only.
3. On dev declining: stop and let the dev install the MCP.

If the MCP **is** available: proceed.

---

## Step 2 — Resolve ticket reference

Accept any of:

| Input | Example | How to resolve |
|---|---|---|
| Bare ticket ID | `SCRUM-374` | Use directly |
| Jira URL | `https://example.atlassian.net/browse/SCRUM-374` | Extract `SCRUM-374` |
| Natural-language reference | *"the navbar bug"* | Search Jira for matching tickets; surface options |
| Sprint reference | *"top of sprint 23"* | Query sprint via MCP; pick top-ranked |

If multiple matches: surface them and ask the dev to pick. If no match: report
and ask the dev to clarify.

---

## Step 3 — Fetch ticket details

Via the Atlassian MCP (`mcp__atlassian__getJiraIssue` or equivalent):

- Summary, description, acceptance criteria
- Status, priority, labels, components
- Assignee, reporter
- Linked issues (depends-on, blocks, related)
- Recent comments (last 10)
- Attachments list (URLs only — do not fetch attachment contents unless
  explicitly requested)

---

## Step 4 — Surface ticket summary to dev

```
🎫 Ticket: SCRUM-374 (In Progress, Priority: High)
   "Navbar collapses incorrectly on mobile <768px"

   Acceptance Criteria:
     - Navbar collapses to hamburger menu at 768px breakpoint
     - Collapsed menu animates open/closed
     - Keyboard navigation works in collapsed state

   Components:  frontend, ui
   Labels:      bug, mobile, navbar
   Linked:      SCRUM-368 (depends on)
   Recent comments: 2 (most recent: "Verified bug on iOS Safari" — 2 days ago)
```

Wait for dev confirmation that the ticket loaded correctly. Allow correction
("wrong ticket", "filter to SCRUM-374's parent epic", etc.).

---

## Step 5 — Prime deliver-work session

Pass to `deliver-work` Step 2 (Ticket establishment, continued):

- The canonical ticket reference: `SCRUM-374`
- The brief (from ticket description + AC)
- The labels and components (used by Step 5 agent matching for harness selection)
- Linked tickets (for traceability)

Tag claude-mem observations for this session with:
- `ticket_ref: SCRUM-374`
- `jira_project: SCRUM`
- `jira_labels: ["bug", "mobile", "navbar"]`

---

## Step 6 — Optional: status transition

If `deliver-work` is in **Step 6 (Plan approved)** or **Step 8 (Final Verify
accepted)** and the dev wants Jira status to track work progress:

@procedures/shared/backlog/lifecycle.md

- On plan approval: transition ticket → "In Progress" (if not already)
- On Final Verify acceptance: transition ticket → "Done"; add closing comment
  with work summary; run completion check from
  `procedures/shared/backlog/completion-check.md`

This is the "never leave a ticket behind" guarantee.

---

## Step 7 — Audit logging

Per `audit/schema.md`:
- `jira_context_invoked` — input form (ID/URL/NL), resolved ticket
- `jira_ticket_loaded` — ticket ID, status, AC count, linked count
- `jira_status_transition` — from, to, comment text (truncated)
- `jira_completion_check` — outcome (per `backlog/completion-check.md`)

---

## Failure modes

| Failure | Handling |
|---|---|
| Atlassian MCP unavailable | Step 1 surfaces remediation; deliver-work proceeds without Jira context |
| Ticket not found | Surface error; ask dev to clarify or pick from candidates |
| MCP request rate-limited / timed out | Retry once with backoff; if still failing, surface to dev with cached context if any |
| Permissions error | Surface explicitly: *"Your Atlassian token lacks read access to project SCRUM. Update permissions and retry, or proceed without ticket context."* |
| Ambiguous natural-language reference | Surface candidates; ask dev to pick |
