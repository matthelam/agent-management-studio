# audit-work Procedure

Read-only investigation across the git repo. Consolidates the OLD `/audit-work`,
`/trace`, and `/investigation` parent procedures into a single skill. Mode is
determined at invocation by scope:

- **Single-ticket mode** (was `/trace`) — follow one work item through its
  lifecycle. *"Why did SCRUM-374 happen the way it did?"*
- **Cross-ticket mode** (was `/audit-work`) — pattern analysis across multiple
  work items. *"Are we consistently following the auth pattern?"*

Both modes use the same machinery (claude-mem observations + agent harnessing +
investigation rules). The output format differs by mode.

---

## Investigation rules (shared)

@procedures/shared/investigation-rules.md

Read-only. No source modification. Cite evidence. Flag uncertainty.

---

## Step 1 — Scope determination

Infer mode from the dev's prompt or ask explicitly:

| Signal | Mode |
|---|---|
| Prompt names a specific ticket / work item | **Single-ticket** |
| Prompt asks "why" about a specific bug or regression | **Single-ticket** |
| Prompt asks for pattern analysis, audit, or trend across multiple items | **Cross-ticket** |
| Prompt names an area without a ticket constraint | **Cross-ticket** with area filter |
| Ambiguous | Ask: *"Single-ticket trace or cross-ticket pattern audit?"* |

Surface the chosen scope to the dev for confirmation.

---

## Step 2 — Agent harnessing

@procedures/shared/agent-harnessing-pattern.md *(referenced from audit-work and
deliver-work alike — see "Agent-harnessing pattern" in docs/architecture.md)*

1. Read seeded `config.json.assembly.agents`.
2. Determine which agent's domain the audit/trace covers:
   - Single-ticket: inferred from the ticket's affected files / Jira labels.
   - Cross-ticket: inferred from the area named in the dev's prompt.
3. Load the relevant agent's specialist + standards as the audit's primary lens.
4. For cross-cutting audits spanning multiple agents' domains: sequentially
   apply each affected agent's perspective; explicitly note perspective
   switches in the report.
5. Surface active perspective(s) to the dev.

---

## Step 3 — Evidence gathering

### Single-ticket mode

Load the ticket's lifecycle:

1. **Claude-mem observations scoped by ticket reference** —
   `curl 'http://127.0.0.1:37777/api/search?project=<name>&query=<ticket-id>'`
   then batch-fetch full observations.
2. **Work item log** if present — `work-items/<ticket-id>.jsonl` (per-work-item
   audit log).
3. **Filesystem scan** of the ticket's affected files (read-only).
4. **Backlog context** if Jira is connected — fetch ticket, comments, related
   tickets via `jira-context`.

Build chronological timeline of events: phase transitions, agent declarations,
resolver decisions, peer consultations, verification results, reclassifications.

### Cross-ticket mode

Load the work-items in scope:

1. **Claude-mem observations scoped by project + filters** — keyword/area filter
   from the prompt; time range; agent filter.
2. **Work-item logs** matching scope filters.
3. **Existing findings** — `findings.json` in the project's findings directory.

Report collection size: *"Auditing N work items matching scope."*

---

## Step 4 — Analysis

### Single-ticket mode (trace logic)

Identify decision points in the timeline:
- For each `resolver_decision`: confidence level vs threshold; tier used; was
  the right tier selected; does the reasoning hold? Flag wrong-tier decisions.
- For each AC at Final Verify: was it verified, with sufficient evidence?
- For Clarity items: how were they resolved, did execution stay true?

If the work item failed verification, was reclassified, or had escalations:
classify root cause using the categories in `investigation-rules.md`:
specification-gap, implementation-error, verification-miss, escalation-failure,
process-deviation, scope-creep, security-vulnerability, standards-violation.

### Cross-ticket mode (audit logic)

Scan for recurring patterns across the collected items:

**Failure patterns** — root cause categories appearing most frequently; agents
involved in repeated failures; phases consistently problematic.

**Escalation patterns** — self-resolve vs peer consult vs human gate ratios;
agents over- or under-escalating.

**Verification patterns** — most-failing ACs; missing evidence types;
verify→execute loop frequency.

**Mode patterns** — Upgrade→Change reclassification rate; Fix root-cause
addressing; per-mode duration averages.

**Trend analysis** (if prior audits available): improving/stable/degrading per
dimension.

For each significant pattern: produce an actionable recommendation (specific
agent, template, process, or artefact to change; routing per
`investigation-rules.md`).

---

## Step 5 — Reporting

### Single-ticket mode output

```
TRACE: <ticket-id>
Mode: <fix|change|upgrade>
Status: <status>
Duration: brief(time) → self_assess(time) → plan(time) → execute(time) → final_verify(time) → done(time)

TIMELINE:
  HH:MM  Phase: <phase> — <summary>
  HH:MM  Self-assess: <agent declarations>
  HH:MM  ...

DECISION POINTS: <count>, <correctness assessment>
VERIFICATION: <pass>/<total> ACs passed with evidence
ROOT CAUSE: <category or N/A>
FINDINGS: <count> — see findings.json
```

### Cross-ticket mode output

```
AUDIT REPORT
Scope: <filters>
Work items analysed: <count>

PATTERNS:
  - <pattern with frequency>

TRENDS:
  - <dimension>: ▲ improving | stable | ▼ degrading

RECOMMENDATIONS:
  1. [<severity>] <specific action>
     Route: <recipient>

FINDINGS GENERATED: <count> (see findings.json)
```

---

## Step 6 — Audit logging

Each significant action emits an event via `audit/service.md` per
`audit/schema.md`:

- `audit_initiated` — scope, mode, filters
- `perspective_changed` — when active agent perspective switches mid-audit
- `findings_recorded` — when new findings are added to `findings.json`
- `audit_completed` — summary of patterns, trends, recommendations, findings

For invocations that produce new findings, the `finding` skill is invoked per
finding to capture the structured artifact (see `procedures/finding.md`).

---

## Read-only reminder

You are auditing, not fixing. For every issue identified, produce a finding via
`finding`. Never modify work items, logs, source code, or agent configurations
directly. Per `investigation-rules.md`: read-only is non-negotiable.
