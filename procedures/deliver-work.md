# /work Procedure

Execute a work item through the single workflow. One of three modes applies: Fix, Change, or Upgrade.

---

## Invocation

```
/work <mode> "<brief description>"
/work <mode> <TICKET-KEY>
/work <mode> sprint <N>
```

**Modes:** `fix`, `change`, `upgrade`

**Brief formats:**
- `"<brief description>"` — manual brief (standard flow, works with or without backlog mode)
- `<TICKET-KEY>` — fetch brief from Jira ticket (requires backlog mode ON)
- `sprint <N>` — pick from top of sprint and work autonomously (requires backlog mode ON)

See `behaviours/backlog/work-invocation.md` for extended invocation syntax.

---

## Pre-flight — Environment Freshness Check

Before starting any work item, check the age of the agent profiles.

### Check

Read the `environment_snapshot.timestamp` from `config.json`. Calculate the age since last update.

If the snapshot age exceeds the configured `stale_threshold_days` (from `config.json`), **challenge the human**:

```
⚠️ Agent profiles were last updated {age} days ago ({snapshot_timestamp}).
Do you want to run /update before starting new work? (yes / no)
```

This is a **mandatory challenge**, not a dismissible warning. The human must explicitly respond.

### Handle Response

| Response | Action |
|----------|--------|
| **Yes** | Invoke `/update` flow. After update completes, return to the `/work` invocation. |
| **No** | Log the human's decision to proceed with stale profiles and continue to Phase 1. |

### Edge Cases

| Scenario | Handling |
|----------|---------|
| No `environment_snapshot` exists | Challenge: "No environment snapshot found. Run `/init` to generate agent profiles, or proceed without environment validation." |
| No `stale_threshold_days` configured | Default to 7 days |
| Snapshot is fresh (within threshold) | Skip challenge, proceed directly to Phase 1 |

### Log

Via audit logging service (`agency/audit/service.md`):

```json
{
  "type": "preflight_check",
  "actor": "system",
  "payload": {
    "check": "environment_freshness",
    "snapshot_age_days": 12,
    "threshold_days": 7,
    "snapshot_timestamp": "ISO-8601",
    "outcome": "stale | fresh | missing",
    "human_decision": "proceed | update | null"
  }
}
```

---

## Backlog Mode Check

After the pre-flight check, determine if backlog mode is active.

### Check

1. Read `.claude/state.json`
2. If a `jira` block exists → backlog mode is **ON**. Load the Jira config (`cloud_id`, `project_key`) into session context.
3. If no `jira` block → backlog mode is **OFF**. Proceed exactly as the standard workflow — zero behaviour change.

Also check the connected project's `config.json` for a `backlog` section (project-level override). Resolution order: project `config.json` `.backlog` > studio `state.json` `.jira` > absent.

### Backlog mode ON — brief routing

When backlog mode is ON, the brief argument determines the flow:

| Brief Argument | Flow |
|----------------|------|
| `"<manual text>"` | Standard brief — backlog mode is ON but no ticket fetch. Proceed to Phase 1 as normal. |
| `<PROJ-NNN>` | Ticket reference — fetch ticket, populate brief via `behaviours/backlog/brief-population.md`, then proceed to Phase 1 clarity assessment. |
| `sprint <N>` | Sprint mode — pick top-ranked 'To Do' item from sprint, populate brief, work to completion, then pick next. See `behaviours/backlog/work-invocation.md`. |

### Backlog mode OFF — standard flow

Proceed directly to Phase 1 with the manual brief text. All existing behaviour is unchanged.

Schema reference: `behaviours/backlog/schemas.md`

---

## Phase 1 — Brief

### Capture

Create a work item record:

```json
{
  "id": "WORK-001",
  "brief": "User-provided description",
  "mode": "fix | change | upgrade",
  "urgency": "normal | elevated | critical",
  "acceptance_criteria": [],
  "agents": [],
  "status": "brief",
  "phases": {},
  "log": "work-items/WORK-001.jsonl"
}
```

When backlog mode is ON and a ticket was fetched, the work item record includes a `backlog` field — see `behaviours/backlog/brief-population.md` for the extended record format.

### Backlog Hook — Ticket Fetched

When backlog mode is ON and a ticket was fetched, immediately transition the Jira ticket to "In Progress" via `behaviours/backlog/lifecycle.md`. This signals to the team that the ticket is being actively worked.

### Clarity Assessment

After recording the brief, each agent evaluates it through the three THINK sub-directives from Posture. This is how agents read any brief — not a separate phase, but the agent's ingrained approach to understanding a task.

**Done State** — Can I picture the finished output? Are acceptance criteria explicit or am I inferring them?

**Decision Authority** — Are there implicit decisions embedded in this task that I am not authorized to make?

**Assumption Risk** — What do I think I know that might be wrong? Am I filling in gaps the brief left open?

Every identified gap and assumption is classified by severity:

- **Critical** — I cannot produce a correct result without this being resolved. Hard blocker.
- **Medium** — I can make a reasonable decision, but the human might disagree.
- **Low** — My specialist knowledge is sufficient. Flagged for transparency only.

The agent produces a **Clarity Report** summarising all items by severity with counts, critical one-liners, and available actions.

### Resolution Dialogue

If the Clarity Report contains Critical items, the agent presents them and waits for the human to resolve each one. Medium and Low items can be resolved by the human, delegated to the agent, or bulk-delegated.

- **Critical** — human must resolve. Delegation attempts are rejected with explanation and structured options.
- **Medium** — delegated items get guided assistance (agent states decision + reasoning, human confirms or overrides).
- **Low** — delegated items are resolved silently by the agent using specialist knowledge.
- **Reclassification** — human can downgrade severity. Agent explains its reasoning first.

The Clarity Report updates progressively after each resolution round until zero Critical items remain.

### Clean brief fast path

If the assessment produces zero Critical items, the agent confirms readiness immediately within the Clarity Report and does not block.

### Log

Via audit logging service (`agency/audit/service.md`):

```json
{
  "type": "phase_transition",
  "actor": "system",
  "payload": { "from": null, "to": "brief" }
}
```

Also log the human gate decision after approval:

```json
{
  "type": "human_gate",
  "actor": "human",
  "payload": {
    "gate": "after_brief",
    "presented": ["work item summary", "clarity report", "resolved acceptance criteria"],
    "decision": "approved | rejected | modified",
    "modifications": null
  }
}
```

### HUMAN GATE — After Brief

Present to human:
- Work item summary with proposed mode and urgency
- Clarity Report (severity table, critical one-liners, resolution status)
- Resolved acceptance criteria, scope, and approach decisions from the Clarity Assessment

**Wait for explicit approval before proceeding.**

### Behaviours

The three evaluation sub-directives (Done State, Decision Authority, Assumption Risk) are defined in `posture.md` under THINK — they are part of agent Posture, not separate behaviour files.

Full Clarity Assessment behaviour definitions: `behaviours/clarity/`

- `clarity-report.md` — Report format, rendering rules, progressive updates, multi-agent assessment, edge cases, persistence, and logging
- `resolution-protocol.md` — Severity classification, resolution dialogue (Critical/Medium/Low), reclassification flow, and logging

---

## Phase 2 — Self-Assess

Each agent evaluates the brief against its specialty and declares involvement:

| Declaration | Meaning |
|-------------|---------|
| **Lead** | Primary domain. Will plan and execute. |
| **Support** | Touches my domain. Will review and consult. |
| **Observe** | Not my domain. Will not participate. |

### Log each declaration

Via audit logging service (`agency/audit/service.md`):

```json
{
  "type": "self_assessment",
  "actor": "agent:frontend-dev",
  "payload": {
    "declaration": "lead",
    "reasoning": "Brief involves UI component changes"
  }
}
```

Update the work item `agents` array with declarations.

---

## Phase 3 — Plan

Lead and support agents produce an execution plan:

- **Files to modify** — list every file that will be touched
- **Approach** — how the change will be implemented
- **Test strategy** — what tests will be added or run
- **Risk assessment** — what could go wrong

Agents reference the persisted Clarity Report: plan against confirmed acceptance criteria, use confirmed scope, apply confirmed approach decisions. If the plan would deviate from a Clarity Report resolution, escalate to the human.

### Mode-specific planning

**Fix:** Include root cause analysis. Present tactical vs root cause options.
**Change:** Include pattern adherence check. Reference project approaches.
**Upgrade:** Include breaking change catalogue. Identify reclassify-to-Change risks.

### Log

Via audit logging service (`agency/audit/service.md`):

```json
{
  "type": "phase_transition",
  "actor": "system",
  "payload": { "from": "self_assess", "to": "plan" }
}
```

Also log the human gate decision:

```json
{
  "type": "human_gate",
  "actor": "human",
  "payload": {
    "gate": "after_plan",
    "presented": ["execution plan", "file list", "test strategy", "risk assessment"],
    "decision": "approved | rejected | modified",
    "modifications": null
  }
}
```

### HUMAN GATE — After Plan

Present to human:
- Execution plan
- File list
- Test strategy
- Risk assessment
- For Fix mode: root cause analysis with tactical vs root cause recommendation

**Wait for explicit approval before proceeding.**

### Backlog Hook — Plan Approved

When backlog mode is ON and the work item has a ticket reference, add a plan summary comment to the Jira ticket via `behaviours/backlog/lifecycle.md`. This provides visibility into the approved approach on the ticket itself.

---

## Phase 4 — Execute

Agents implement the approved plan.

### Execution rules

1. Follow the plan. If the plan needs to change, return to Phase 3.
2. Apply Posture directives throughout: THINK, MINIMIZE, CUT, VERIFY.
3. Apply relevant Standards for each agent's output.
4. Use the resolver for every decision with uncertainty:
   - Confidence above threshold → self-resolve and log
   - Confidence below threshold → peer consult and log
   - Ambiguity or irreversible → human gate
5. Peer consultation occurs during this phase — agents consult structured pairs before cross-boundary changes.

### Fix mode — execution specifics

- Implement the approach the human approved (tactical or root cause)
- Verify the fix addresses the symptom
- Run regression tests to confirm nothing else broke

### Change mode — execution specifics

- Implement against acceptance criteria
- Follow project patterns (reference `patterns.md` and `approaches.md`)
- Add tests for new behaviour
- Consult peer on cross-cutting changes

### Upgrade mode — execution specifics

- Make only mechanical/technical changes
- **Reclassify checkpoint:** If you need to modify business logic or change test expectations, STOP. Log the reclassification and switch to Change mode. Do not proceed with Upgrade mode.
- Run existing test suite after each significant change

### Log

Via audit logging service (`agency/audit/service.md`):

```json
{
  "type": "phase_transition",
  "actor": "system",
  "payload": { "from": "plan", "to": "execute" }
}
```

Log resolver decisions as they occur (see `behaviours/resolver.md` and `agency/audit/schema.md` for `resolver_decision` schema).

---

## Phase 5 — Final Verify

Run the verifier against every acceptance criterion.

### Per-AC verification

For each acceptance criterion:
1. State the criterion
2. Evaluate: PASS or FAIL
3. Provide specific evidence (test results, code references, review outcomes)
4. If FAIL: return to Phase 4 with the specific failure

The verifier cross-references the Clarity Report: verify against resolved done state, confirm approach adherence, catch drift from Clarity Report resolutions.

### Mode-specific final checks

**Fix:** Symptom resolved? Root cause addressed? Zero regressions?
**Change:** All ACs pass? Patterns followed? Tests added? No scope creep?
**Upgrade:** Zero business logic changes? All existing tests pass unmodified? No reclassification needed?

### Log

Via audit logging service (`agency/audit/service.md`):

```json
{
  "type": "phase_transition",
  "actor": "system",
  "payload": { "from": "execute", "to": "final_verify" }
}
```

One `verification_result` entry per acceptance criterion:

```json
{
  "type": "verification_result",
  "actor": "agent:<name>",
  "payload": {
    "ac_index": 1,
    "ac_text": "Login validates email format",
    "clarity_item_id": "clarity-001",
    "status": "pass | fail",
    "evidence": "Unit test login-form.test.ts:L45 passes",
    "drift_detected": false
  }
}
```

Also log the human gate decision:

```json
{
  "type": "human_gate",
  "actor": "human",
  "payload": {
    "gate": "after_final_verify",
    "presented": ["verification results", "change summary", "resolver escalations", "test results"],
    "decision": "approved | rejected | modified",
    "modifications": null
  }
}
```

### HUMAN GATE — After Final Verify

Present to human:
- Per-AC verification results with evidence
- Summary of changes made
- Any resolver escalations that occurred
- Test results

**Wait for explicit acceptance before closing.**

### Backlog Hook — Final Verify Accepted

When backlog mode is ON and the work item has a ticket reference:

1. Run the completion check via `behaviours/backlog/completion-check.md`
2. Transition the Jira ticket to "Done" via `behaviours/backlog/lifecycle.md`
3. Add a closing comment with the work summary

This is the "never leave a ticket behind" guarantee. See `behaviours/backlog/completion-check.md` for the full procedure.

---

## Work Item Lifecycle

```
brief → self_assess → plan → execute → final_verify → done
                        ↑                    |
                        └────────────────────┘
                        (on verification failure)
```

Status transitions are logged. A work item is only `done` after human acceptance at the final gate.

---

## Urgency Modifier

Applied on top of any mode. Adjusts Posture behaviour:

| Level | MINIMIZE | CUT | Gates |
|-------|----------|-----|-------|
| Normal | Standard | Standard | All three |
| Elevated | Tighter — defer nice-to-haves | Aggressive | All three |
| Critical | Minimum viable path | Maximum constraint | Brief gate may be expedited |

Urgency never removes quality gates or verification. It tightens scope.
