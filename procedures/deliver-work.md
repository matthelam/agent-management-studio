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

## Cognitive Team Mode (v2)

After the backlog mode check and before Phase 1, resolve the cognitive team
that will execute this work item. Three modes; selected by silent default
or by keyword pattern-match against the dev's prompt.

### Resolver

```
Default (no team-related keyword in prompt — 99% of work):
  → SINGLE-AGENT mode
  → harness = config.json.assembly.primary_harness_for_single_mode (typically `empiricist`)
  → no lenses applied (unless project's default_lenses are always-on for the work)

Keyword detected: "team" | "swarm" | "second opinion" | "multiple perspectives" | "get a team":
  → DEFAULT-TEAM mode
  → harnesses = config.json.assembly.cognitive_team
  → lenses = config.json.assembly.default_lenses

Keyword detected: "let me define the team" | "custom team" | "audit this with [list]" | "use [harness] and [harness]":
  → CUSTOM-TEAM mode
  → harnesses = parsed from prompt
  → lenses = parsed from prompt OR project default_lenses
```

No DQ computation. No interactive prompting. Pattern-match the prompt; default
to single agent silently.

### Sub-agent dispatch

Each cognitive harness is implemented as a Claude Code sub-agent via the
`Agent` tool. For each harness in the resolved team:

1. Read `harnesses/<name>.md` from the seeded `.claude/harnesses/` directory.
2. Apply concern lens overlays per `lenses/<lens>.md` — concatenate the
   lens's `prompt overlay` to the harness's `pillar_implementation.pillar_1_input_vector.posture_anchor`.
3. Invoke `Agent` with:
   - `model` = harness's `model` field (claude-sonnet or claude-opus)
   - `prompt` = constructed posture_anchor (harness + lens overlays)
   - `description` = "<harness-name> harness for <ticket-id>"
4. Pass shared context: ticket details, clarity report, applicable patterns
   slice, applicable approaches slice, applicable domain skills (proximity-loaded).

### Mode-specific phase mapping

**SINGLE-AGENT mode:** Single harness executes Phases 1-5 as defined below.
Self-Assessment (Phase 2) collapses into one declaration. Mode is silent —
no team-related output to dev unless they ask.

**DEFAULT-TEAM mode:** Each harness executes Phases 2-5 in parallel; their
outputs feed into a synthesis step (Synthesizer harness on Opus) at each phase
boundary. Phases run as:

- Phase 2 (Self-Assess) — each harness self-assesses Lead/Support/Observe;
  the synthesizer reconciles to determine which harness is Lead.
- Phase 3 (Plan) — Lead harness drafts; Support harnesses critique;
  synthesizer reconciles into single plan.
- Phase 4 (Execute) — Lead executes; Support harnesses review changes
  inline (post-tool-use observation); synthesizer reconciles only at phase
  boundary, not per tool call (cost control).
- Phase 5 (Final Verify) — each harness independently verifies against ACs;
  synthesizer reconciles into single per-AC pass/fail with attributed
  evidence.

**CUSTOM-TEAM mode:** Same as default-team but with custom harness/lens set.
Dev may also specify altitude override per harness for this work item.

### Audit-log the mode resolution

Immediately after resolving the team, enumerate which domain skills are active
in context (those whose `description` proximity trigger matches the work scope
from the brief + ticket path). Log them alongside the harness and lenses so the
trace has the complete cognitive picture at ticket start.

```json
{
  "type": "cognitive_team_resolved",
  "actor": "system",
  "payload": {
    "mode": "single | default-team | custom-team",
    "trigger": "silent_default | keyword_match | dev_specified",
    "matched_keyword": "team | swarm | second opinion | null",
    "harnesses": ["empiricist"],
    "primary_harness": "empiricist",
    "synthesis_harness": "synthesizer | null",
    "lenses": [],
    "skills_active": [
      {
        "skill_id": "<skill-id from .claude/skills/>",
        "load_reason": "proximity — <which path pattern or keyword triggered it>"
      }
    ]
  }
}
```

`skills_active` must list every domain skill whose description proximity trigger
matches the current work scope. If no domain skills match, emit an empty array
`[]` — never omit the field.

### Emit `cognitive_state_changed` when the cognitive configuration shifts mid-ticket

If at any point after `cognitive_team_resolved` the developer overrides the
mode, the resolver escalates to a peer harness, or a scope shift causes a
different skill set to become active, emit:

```json
{
  "type": "cognitive_state_changed",
  "actor": "system | human",
  "payload": {
    "phase": "<current phase>",
    "trigger": "dev_override | escalation | resolver_peer_consult | skill_proximity_change",
    "from": {
      "harnesses": ["<previous>"],
      "lenses": [],
      "skills_active": ["<previous skill ids>"]
    },
    "to": {
      "harnesses": ["<new>"],
      "lenses": ["<new>"],
      "skills_active": ["<new skill ids>"]
    },
    "change_description": "<one sentence: what changed and why>"
  }
}
```

Emit one event per discrete change. Do not batch multiple changes into one event.

### Domain skills auto-load via proximity (always-on, regardless of team mode)

Independent of harness team selection: as the work touches files, generated
domain skills (per-tech, dynamic — see learn-codebase) auto-load via
proximity triggers in their descriptions. The Lead harness uses these as
its tech-specific knowledge layer regardless of which harness it is.

Example: Lead harness is Empiricist; work is in `packages/ui-sitecore/`. The
seeded `sitecore-knowledge` skill triggers on proximity, providing
Sitecore-specific patterns / GUARD RAILS / CLI references / doc-fallback
to the Empiricist's posture.

This means: harness = HOW; domain skill = WHAT IS. Both layer on top of
posture + standards (universal).

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

Emit the phase transition immediately when Phase 1 begins — do not defer:

```bash
WORK_ID="$(jq -r '.audit.current_work_item' .claude/config.json 2>/dev/null)"
AUDIT_FILE=".claude/audit/work-items/${WORK_ID}.jsonl"
printf '{"timestamp":"%s","type":"phase_transition","actor":"system","payload":{"from":null,"to":"brief"}}\n' \
  "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)" >> "$AUDIT_FILE"
```

Also log the human gate decision after approval:

```bash
printf '{"timestamp":"%s","type":"human_gate","actor":"human","payload":{"gate":"after_brief","presented":["work item summary","clarity report","resolved acceptance criteria"],"decision":"approved|rejected|modified","modifications":null}}\n' \
  "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)" >> "$AUDIT_FILE"
```
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
- **Test strategy** — what tests will be added or run (see TDD REQUIREMENT below)
- **Risk assessment** — what could go wrong

Agents reference the persisted Clarity Report: plan against confirmed acceptance criteria, use confirmed scope, apply confirmed approach decisions. If the plan would deviate from a Clarity Report resolution, escalate to the human.

**TDD REQUIREMENT (non-negotiable):** The test strategy must be written before implementation begins. For every AC:
- State what unit/integration test will cover it and the expected assertion
- If the AC involves a UI component, state which Storybook story will cover it and how it will be visually verified
- If the project has a Storybook domain skill, **explicitly invoke it before writing any `.stories.tsx` file** — the Storybook skill is a mandatory pre-condition for story authoring, not optional
- Tests must be written (and failing) before the implementation code that makes them pass — TDD red-green-refactor

This is a harness crux: an untested AC is an unverifiable AC. A plan without auditable test coverage is incomplete and must not be approved.

### Mode-specific planning

**Fix:** Include root cause analysis. Present tactical vs root cause options.
**Change:** Include pattern adherence check. Reference project approaches.
**Upgrade:** Include breaking change catalogue. Identify reclassify-to-Change risks.

### Log

Emit the phase transition immediately when Phase 3 begins — do not defer:

```bash
WORK_ID="$(jq -r '.audit.current_work_item' .claude/config.json 2>/dev/null)"
AUDIT_FILE=".claude/audit/work-items/${WORK_ID}.jsonl"
printf '{"timestamp":"%s","type":"phase_transition","actor":"system","payload":{"from":"self_assess","to":"plan"}}\n' \
  "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)" >> "$AUDIT_FILE"
```

Also log the human gate decision:

```bash
printf '{"timestamp":"%s","type":"human_gate","actor":"human","payload":{"gate":"after_plan","presented":["execution plan","file list","test strategy","risk assessment"],"decision":"approved|rejected|modified","modifications":null}}\n' \
  "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)" >> "$AUDIT_FILE"
```

### HUMAN GATE — After Plan

Present to human:
- Execution plan
- File list
- Test strategy (including per-AC test assertions and Storybook story plan for UI ACs)
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
6. **RESOLVER LOGGING RULE (non-negotiable):** Every resolver decision must be logged inline immediately when it occurs — do not batch. Zero `resolver_decision` events in a non-trivial work item is a protocol violation detectable in audit. Use this emit after each decision:

```bash
WORK_ID="$(jq -r '.audit.current_work_item' .claude/config.json 2>/dev/null)"
AUDIT_FILE=".claude/audit/work-items/${WORK_ID}.jsonl"
printf '{"timestamp":"%s","type":"resolver_decision","actor":"agent:<name>","payload":{"decision":"<what was decided>","confidence":"high|medium|low","method":"self|peer|human","rationale":"<why>"}}\n' \
  "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)" >> "$AUDIT_FILE"
```

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

Emit the phase transition immediately when Phase 4 begins — do not defer:

```bash
WORK_ID="$(jq -r '.audit.current_work_item' .claude/config.json 2>/dev/null)"
AUDIT_FILE=".claude/audit/work-items/${WORK_ID}.jsonl"
printf '{"timestamp":"%s","type":"phase_transition","actor":"system","payload":{"from":"plan","to":"execute"}}\n' \
  "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)" >> "$AUDIT_FILE"
```

Log resolver decisions inline as they occur — do not batch (see Phase 4 resolver logging rules above).

### Emit `skill_triggered` each time a domain skill actively shapes a decision

When you explicitly read a domain skill to resolve an implementation question —
not just because it is passively present in context — emit:

```json
{
  "type": "skill_triggered",
  "actor": "agent:<harness-name>",
  "payload": {
    "skill_id": "<skill-id>",
    "phase": "execute",
    "reason": "<one sentence: what question you were resolving>",
    "outcome": "pattern_applied | guard_rail_enforced | doc_fallback_used | no_match"
  }
}
```

Emit once per consultation. Do not emit for passive context presence — only when
the skill's content directly influenced a decision (pattern chosen, GUARD RAIL
enforced, doc-fallback invoked, or skill checked and found inapplicable).

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

**RENDERING EVIDENCE RULE (non-negotiable):** If any AC contains the words "render", "display", "visible", "Storybook", or "browser", the evidence field MUST include a Playwright screenshot. Code evidence (file existence, import presence, TypeScript checks) is insufficient for these ACs and will be treated as a protocol violation in audit. No rendering AC may be marked PASS without visual evidence.

### Mode-specific final checks

**Fix:** Symptom resolved? Root cause addressed? Zero regressions?
**Change:** All ACs pass? Patterns followed? Tests added? No scope creep?
**Upgrade:** Zero business logic changes? All existing tests pass unmodified? No reclassification needed?

### Log

Emit the phase transition immediately when Phase 5 begins — do not defer:

```bash
WORK_ID="$(jq -r '.audit.current_work_item' .claude/config.json 2>/dev/null)"
AUDIT_FILE=".claude/audit/work-items/${WORK_ID}.jsonl"
printf '{"timestamp":"%s","type":"phase_transition","actor":"system","payload":{"from":"execute","to":"final_verify"}}\n' \
  "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)" >> "$AUDIT_FILE"
```

One `verification_result` entry per acceptance criterion (emit immediately per AC, not batched):

```bash
printf '{"timestamp":"%s","type":"verification_result","actor":"agent:<name>","payload":{"ac_index":<N>,"ac_text":"<text>","status":"pass|fail","evidence":"<evidence>","drift_detected":false}}\n' \
  "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)" >> "$AUDIT_FILE"
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
