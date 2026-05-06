# Clarity Report

The Clarity Report is the structured output of the Clarity Assessment during the Brief phase. It is the primary interface between the assessment engine and the human.

---

## Report Structure

### Summary Table

Render the summary table showing counts by severity:

```
Clarity Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
| Severity | Gaps | Assumptions | Resolved |
|----------|------|-------------|----------|
| Critical |  0   |      0      |    0     |
| Medium   |  0   |      0      |    0     |
| Low      |  0   |      0      |    0     |
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Counts reflect the current state. The Resolved column tracks items resolved through any method (human-resolved, delegated, reclassified).

### Critical Items Section

List every Critical item with a concise one-liner explaining _what_ and _why_:

```
Critical items (must resolve before work begins):
• [Gap] No acceptance criteria — multiple valid interpretations of "done" exist
• [Gap] Architecture decision required — theme provider vs CSS variables
• [Assumption] System preference detection assumed in scope — brief does not mention it
```

Critical items are always listed individually. They are hard blockers.

### Action Guidance

After the critical items, show available actions for remaining items:

```
For Medium and Low items, you can:
  → Resolve them yourself (provide your decision)
  → Delegate to me (I'll explain my reasoning)
  → "Handle all mediums" / "Handle all lows" (bulk delegation)
```

---

## Rendering Rules

1. **Always render the full table** — even when all counts are zero (clean brief scenario).
2. **Critical one-liners must be concise and actionable** — state the issue and why it blocks, nothing more.
3. **Use item type prefix** — `[Gap]` or `[Assumption]` before each one-liner.
4. **Order within severity** — list gaps before assumptions within each severity level.
5. **Do not lecture** — if the brief is vague, report the high critical count honestly. Do not comment on brief quality.

---

## Progressive Updates

After each resolution round, the Clarity Report re-renders to reflect the current state. This gives the human a clear visual of progress toward the exit condition (zero unresolved Critical items).

### Update Triggers

The Clarity Report re-renders after any of these actions:

- Human resolves one or more items
- Human delegates one or more items (and agent completes guided assistance or autonomous handling)
- Human reclassifies one or more items
- Bulk delegation completes ("handle all mediums", "handle all lows")
- Any combination of the above in a single round

### Update Behaviour

**Counts update:** The summary table recalculates — gap and assumption counts reflect only **open** items per severity; resolved column increments for every item no longer open; reclassified items move between severity rows.

**Critical items re-listed:** After each update, only open Critical items appear. Resolved or reclassified items are removed from the list.

**Mixed actions in a single round:** All changes are applied before re-rendering. The human sees one updated report, not multiple intermediate states.

### Readiness Confirmation

When the Critical count reaches zero, the agent displays:

```
Clarity Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
| Severity | Gaps | Assumptions | Resolved |
|----------|------|-------------|----------|
| Critical |  0   |      0      |    3     |
| Medium   |  0   |      1      |    2     |
| Low      |  0   |      0      |    2     |
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

All critical items resolved. Ready to proceed to Plan phase.
```

The readiness confirmation triggers automatically. The human can still resolve remaining Medium or Low items if they wish, or allow the workflow to continue.

---

## Multi-Agent Assessment

When `/work` dispatches to multiple agents, each agent that declared **Lead** or **Support** runs its own Clarity Assessment independently using its own specialist knowledge, standards, scope boundaries, and Posture sub-directives. Agents that declared **Observe** do not run a Clarity Assessment.

### Consolidated View

The human sees a single consolidated report that merges all agent assessments. Each item is prefixed with the originating agent:

```
Clarity Report (consolidated)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
| Severity | Gaps | Assumptions | Resolved |
|----------|------|-------------|----------|
| Critical |  3   |      1      |    0     |
| Medium   |  2   |      2      |    0     |
| Low      |  1   |      3      |    0     |
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Critical items (must resolve before work begins):
• [frontend-dev] [Gap] No component architecture specified — modal vs inline vs page
• [backend-dev] [Gap] API contract undefined — no endpoint shape agreed
• [frontend-dev] [Gap] No error state design — multiple UX approaches possible
• [backend-dev] [Assumption] Assumes REST — brief does not specify API style
```

### Cross-Agent Blocking

**A Critical item from any agent blocks the entire workflow.** Not just that agent's work — all agents wait. Agent work is interdependent: an unresolved API contract Critical blocks both the backend and frontend from planning.

### Deduplication

When multiple agents flag the same issue:

1. **Identical items** — merge into one, retain the **highest** severity.
2. **Related items** — keep both but group them visually with agent attribution.
3. **Independent items** — list separately.

### Cross-Agent Resolution Propagation

When the human resolves an item, the resolution applies to all contributing agents. If resolving one agent's Critical also resolves another agent's Medium on the same topic, the Medium is auto-resolved with a note in the log.

### Per-Agent Readiness

The workflow proceeds only when **all** agents have zero unresolved Critical items.

---

## Edge Cases

Every scenario flows through the same Clarity Report format. There are no special-case UIs or alternative flows. The report's severity counts naturally communicate the brief's readiness level.

### Clean Brief

The assessment produces zero Critical items. Render the report with accurate counts (likely zero criticals, a few lows). Confirm readiness immediately. Do not block.

```
No critical items. Ready to proceed.

Medium and Low items noted for transparency — resolve, delegate, or proceed.
```

**Key rule:** The clean brief is a validation that the assessment ran and found nothing blocking. It is not a skip — always run the full assessment.

### Vague Brief

The brief is sparse or ambiguous (e.g., "fix the thing", "make it better"). The three Posture sub-directives will surface many gaps — the Critical count will be high.

Do not lecture about brief quality. Do not say "this brief is too vague." Simply present the gaps — they speak for themselves. Wait for the human to resolve them through the normal resolution flow.

**Key rule:** The vague brief is not an error condition. It is a brief with a high critical count.

### Contradictory Brief

The brief asks for something that conflicts with established project patterns, standards, or previous decisions. The contradiction surfaces through the Assumption Risk or Decision Authority sub-directives and is classified Critical (the agent cannot know which takes precedence).

Present the contradiction clearly:

```
• [Gap] Brief requests X, but project patterns specify Y. Which takes precedence?
```

The human resolves by choosing one direction. The resolution is recorded and carried into Plan and Execute.

**Key rule:** Contradictions are decisions that need human input, not errors in the brief.

---

## Underlying Data Format

```json
{
  "work_item_id": "WORK-001",
  "agent": "frontend-dev",
  "timestamp": "ISO-8601",
  "items": [
    {
      "id": "clarity-001",
      "lens": "done-state",
      "type": "gap",
      "description": "No acceptance criteria — multiple valid interpretations exist",
      "reasoning": "Agent cannot verify delivery without knowing what done looks like",
      "severity": "critical",
      "classification_reasoning": "Multiple valid interpretations with no way to choose",
      "status": "open",
      "resolution": null,
      "resolved_by": null
    }
  ],
  "summary": {
    "critical": { "gaps": 0, "assumptions": 0, "resolved": 0 },
    "medium": { "gaps": 0, "assumptions": 0, "resolved": 0 },
    "low": { "gaps": 0, "assumptions": 0, "resolved": 0 }
  }
}
```

### Item Status Values

| Status | Meaning |
|--------|---------|
| `open` | Not yet resolved |
| `resolved` | Resolved by human providing a decision |
| `delegated` | Delegated to agent — agent decided with reasoning |
| `reclassified` | Severity changed by human — item moved to new tier |

---

## Persistence

The final Clarity Report (with all resolutions) persists as part of the work session. It serves as documentation, input for downstream phases, and audit trail.

### What is Persisted

- Full Clarity Report table — final state with all counts and resolved column
- All items with resolutions — human-resolved, delegated, and reclassified
- Agent reasoning — for every delegated decision, the agent's stated reasoning
- Resolved acceptance criteria, scope, and approach decisions

### Feeding into Plan Phase

The Plan phase receives the persisted Clarity Report as structured input. Agents reference it to plan against confirmed acceptance criteria, use confirmed scope, and apply confirmed approach decisions. **Resolved items are commitments, not suggestions.** If the plan would deviate from a Clarity Report resolution, the agent must escalate to the human.

### Feeding into Verify Phase

The Final Verify phase references the persisted Clarity Report to verify against resolved done state, confirm approach adherence, and catch drift. If the execution phase introduced decisions that contradict Clarity Report resolutions, the verifier flags them.

---

## Logging

Log the following events via the audit logging service (`agency/audit/service.md`). Use schemas from `agency/audit/schema.md`.

**On assessment initiation** (before items are identified):

```json
{
  "type": "clarity_assessment_initiated",
  "actor": "agent:<name>",
  "payload": {
    "agents": ["frontend-dev"],
    "brief_length_chars": 342
  }
}
```

**For each item identified** (one entry per gap or assumption):

```json
{
  "type": "clarity_item",
  "actor": "agent:<name>",
  "payload": {
    "item_id": "clarity-001",
    "lens": "done-state",
    "item_type": "gap",
    "severity": "critical",
    "description": "No acceptance criteria — multiple valid interpretations exist"
  }
}
```

**On final report** (after all items resolved, before human gate):

```json
{
  "type": "clarity_report_final",
  "actor": "system",
  "payload": {
    "agents": ["frontend-dev"],
    "resolution_rounds": 2,
    "summary": {
      "critical": { "identified": 2, "resolved": 2 },
      "medium": { "identified": 3, "resolved": 3 },
      "low": { "identified": 1, "resolved": 1 }
    },
    "outcome": "ready"
  }
}
```
