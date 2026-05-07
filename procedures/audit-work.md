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

## Step 2 — Cognitive team resolution (v2)

Same resolver as `deliver-work` (silent single + keyword triggers + custom
override). Applied to audit-work with audit-specific defaults.

### Resolver

```
Default (no team-related keyword in prompt — 99% of work):
  → SINGLE-AGENT mode
  → harness = config.json.assembly.primary_harness_for_single_mode (typically `empiricist`)
  → For audit-work specifically, project may override to `skeptic` for
    cross-ticket adversarial audits via assembly.audit_primary_harness if set.
  → no lenses applied (unless project's default_lenses are always-on)

Keyword detected: "team" | "swarm" | "second opinion" | "multiple perspectives":
  → DEFAULT-TEAM mode
  → harnesses = config.json.assembly.cognitive_team
  → For audit-work, the synthesizer is always added (or already present in
    default_team) — it's the natural reconciler for parallel audits.
  → lenses = config.json.assembly.default_lenses

Keyword detected: "audit this from a security perspective" / "performance audit"
| "accessibility audit" | similar lens-specific phrases:
  → CUSTOM-TEAM mode (lens-driven)
  → harness = primary_harness_for_single_mode OR skeptic
  → lens = matched lens (security | performance | accessibility | devils_advocate)
  → Often: skeptic + security; specifist + accessibility; architect + performance.

Keyword detected: "let me define the team" | "audit this with [list]":
  → CUSTOM-TEAM mode
  → harnesses + lenses parsed from prompt
```

### Sub-agent dispatch

Each harness in the resolved team is invoked as a Claude Code sub-agent via
the `Agent` tool (same pattern as deliver-work).

For each harness:
1. Read `harnesses/<name>.md`.
2. Apply concern lens overlays (concatenate to posture_anchor).
3. Invoke `Agent` with the harness's `model` and the constructed posture.
4. Pass shared context: scope (single or cross-ticket), evidence corpus
   (claude-mem observations + work-item logs + filesystem reads), proximity-loaded
   domain skills.

### Mode-specific execution

**SINGLE-AGENT mode:** Single harness performs Steps 3-5 (evidence gathering,
analysis, reporting). No synthesis step — output is direct.

**DEFAULT-TEAM mode:** Each harness performs Steps 3-4 in parallel against
the same evidence corpus. A Synthesizer harness reconciles their outputs in
Step 5:
- Findings reinforced by ≥2 harnesses → high-confidence claim
- Findings contradicted between harnesses → flagged for human review with
  both views surfaced
- Findings unique to one harness → reported with attribution to the
  perspective ("the Skeptic identified..." / "the Architect noted...")

**CUSTOM-TEAM mode:** As default-team but with the custom harness/lens set.

### Audit-log the resolution

```json
{
  "type": "cognitive_team_resolved",
  "actor": "system",
  "payload": {
    "skill": "audit-work",
    "scope": "single-ticket | cross-ticket | mixed",
    "mode": "single | default | custom",
    "trigger": "silent_default | keyword_match | dev_specified",
    "harnesses": ["..."],
    "lenses": ["..."],
    "primary_harness": "...",
    "synthesis_harness": "synthesizer | null"
  }
}
```

### Domain skills auto-load via proximity

As the audit traverses files, generated domain skills auto-load (same
mechanism as deliver-work). The harnesses use them as tech-specific
knowledge layers during analysis.

This separates HOW (harness) from WHAT IS (domain skill) for read-only
investigation work.

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
