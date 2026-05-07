# Elaboration — Instruction Plan to Jira Backlog

Elaboration is not a special mode. Every work request produces an instruction plan broken down into Features, Stories, and Subtasks following scrum methodology. When backlog mode is ON and the human approves the plan, the hierarchy is automatically created in Jira.

---

## The Standard Flow (Always Happens)

This is what the studio already does, regardless of backlog mode:

1. The orchestration agent receives a work request
2. It produces an instruction plan with **Features** (Epics) → **Stories** → **Subtasks**
3. Each Story is independent — completable without waiting on other stories (unless an explicit dependency exists)
4. Each Subtask is sized for a single sub-agent
5. Dependencies between stories are identified and recorded
6. The plan is presented for human approval

---

## What Backlog Mode Adds

When backlog mode is ON (`state.json` contains a `jira` block) and the human approves the instruction plan:

1. For each Feature: `createJiraIssue(cloudId, projectKey, "Epic", ...)`
2. For each Story: `createJiraIssue(cloudId, projectKey, "Story", ..., parent=epicKey)`
3. For each Subtask: `createJiraIssue(cloudId, projectKey, "Sub-task", ..., parent=storyKey)`
4. For each dependency: add Jira issue links ("is blocked by")
5. Add a summary comment to the parent Epic with the full hierarchy and execution order

This is **automatic on approval** — the human does not need to ask for it. If `--jira` is active, plan approval = Jira creation.

---

## Splitting Rules

### Story Independence

Each Story must be completable independently of other stories unless an explicit dependency exists. This means:

- A Story's scope is self-contained — it does not require another Story's output to begin
- If a Story requires another Story's output → that is a **dependency**, expressed as a Jira link
- Dependencies should be minimised — prefer parallel-capable stories over sequential chains

### Single Specialist Domain

Each Story should map to a single specialist domain where possible:

- If a Story requires only frontend work → assign to `frontend-dev`
- If a Story requires only backend work → assign to `backend-dev`
- If a Story requires two specialists → **split into two Stories**

Splitting by specialist domain ensures each Story can be delegated to one agent without cross-cutting coordination overhead.

### Subtask Sizing

Each Subtask must be completable by **one agent in one work session**:

- A Subtask is a single, atomic piece of work
- If a subtask requires more than one file group or one conceptual change → split it further
- Subtasks within a Story can be worked in parallel unless they have internal ordering

### Reviewer Assignment

Code review and security audit are **peer consultations**, not dependencies:

- A Story that produces code will be reviewed by `code-review` — this is a peer consultation during Execute phase
- A Story that touches security-sensitive areas will be audited by `security-audit` — this is also a peer consultation
- Do NOT create separate Stories for "review" or "audit" — these happen within the executing Story's workflow

### Dependency Rules

- If a Subtask requires waiting for another agent's **non-review** output → that is a dependency, express as a Jira link
- Review and audit are NOT dependencies — they happen inline during Execute
- Cross-feature dependencies should be documented at the Story level
- Within a feature, prefer a topological ordering that minimises blocking

---

## Jira Issue Content

### Epic (Feature)

```
Summary: <Feature title>
Description:
  ## Overview
  <Feature description>

  ## Stories
  <Numbered list of stories in this feature>

  ## Dependencies
  <Cross-feature dependencies if any>
```

### Story

```
Summary: <Story title>
Description:
  ## Context
  <What this story delivers and why>

  ## Acceptance Criteria
  - [ ] <AC 1>
  - [ ] <AC 2>

  ## Files
  <Expected files to create or modify>

  ## Specialist
  <Assigned specialist agent>

  ## Dependencies
  <Blocked by: PROJ-NNN if any>
```

### Subtask

```
Summary: <Subtask title>
Description:
  ## Task
  <Specific atomic task>

  ## Agent
  <Assigned agent>

  ## Expected Output
  <What this subtask produces>
```

---

## Audit Logging

Via audit logging service (`agency/audit/service.md`):

```json
{
  "type": "backlog_elaboration",
  "session_id": "SESSION-...",
  "work_item_id": "WORK-001",
  "actor": "system",
  "payload": {
    "epics_created": 3,
    "stories_created": 10,
    "subtasks_created": 25,
    "dependencies_linked": 8,
    "jira_keys": {
      "epics": ["SCRUM-100", "SCRUM-101", "SCRUM-102"],
      "stories": ["SCRUM-103", "SCRUM-104"],
      "subtasks": ["SCRUM-110", "SCRUM-111"]
    }
  }
}
```

---

## Execution After Creation — Recursive Completion Loop

Once the hierarchy exists in Jira, the orchestration agent executes the work items in dependency order.

### Topological Sort

1. Build a dependency graph from the Jira issue links
2. Compute a topological sort — items with no unresolved dependencies come first
3. Among items with equal dependency depth, prefer the rank order from Jira (sprint ordering)

### Execution Loop

```
1. Find all unblocked subtasks (dependencies satisfied, status = 'To Do')

2. If no unblocked subtasks remain:
   a. Check if all subtasks are Done → feature complete
   b. If blocked subtasks exist → report blocked items and dependencies to human
   c. Exit loop

3. Pick the first unblocked subtask (topological order)

4. Execute through the 5-phase workflow:
   Brief → Self-Assess → Plan → Execute → Final Verify

5. On completion:
   a. Transition subtask to Done
   b. Check if parent Story has all subtasks Done → transition Story to Done
   c. Check if parent Epic has all Stories Done → transition Epic to Done
   d. Return to step 1
```

### Recursive Completion Cascade

When a subtask completes, check upward:

| Level | Check | Action |
|-------|-------|--------|
| Subtask → Story | All sibling subtasks Done? | Transition Story to Done |
| Story → Epic | All child Stories Done? | Transition Epic to Done, add summary comment |

This cascade runs automatically after each subtask completion. It uses the same dynamic transition resolution from `lifecycle.md`.

### Human Intervention Points

- **Skip an item:** Human can instruct the agent to skip a blocked or problematic subtask. The agent logs the skip and proceeds to the next unblocked item.
- **Re-prioritise:** Human can change the execution order. The agent re-queries Jira for the updated rank.
- **Stop:** Human can halt execution at any point. The agent reports progress and exits.

### Progress Reporting

After each subtask completion:

```
✓ SCRUM-110 — Done
  Story SCRUM-103: 3/5 subtasks complete
  Epic SCRUM-100: 2/4 stories complete
  Next: SCRUM-112 (unblocked)
```

On feature completion:

```
✓ Feature complete: SCRUM-100 — Backlog Configuration
  Stories: 3/3 Done
  Subtasks: 8/8 Done

  Moving to next feature: SCRUM-101...
```
