# Cognitive Architecture (v2)

How AMS v2 separates *how agents think* (cognitive harnesses) from *what they
know* (domain skills) from *what they do* (procedural skills).

---

## The three-layer separation

v1 conflated two things in `templates/specialists/*.md`:

1. **Domain knowledge** — what a frontend-dev knows about React, CVA, Tailwind, etc.
2. **Cognitive style** — how a frontend-dev tends to think (user-focused, detail-oriented).

These are independent in reality. A senior dev can be a Skeptic on Monday
(security review) and a Synthesizer on Tuesday (proposing an abstraction)
applied to the same domain knowledge.

v2 separates them into three distinct layers:

| Layer | What it captures | Where it lives | How it's invoked |
|---|---|---|---|
| **Cognitive harness** | HOW the agent thinks (cognitive style) | `harnesses/<name>.md` | Dispatched via Claude Code's `Agent` tool with the harness's model + posture_anchor |
| **Concern lens** | What dimension of concern is foregrounded | `lenses/<name>-lens.md` | Applied as overlay on top of any harness |
| **Domain skill** | WHAT the agent knows about a tech | `templates/skills/` (procedural) + dynamically generated `<tech>-knowledge` (domain) | Procedural: intent-matched. Domain: proximity-triggered. |

A team is `[harnesses] + [lenses]` operating with `[domain-skills]` available.

---

## Cognitive harnesses

Source for the framework: Matt Helam, *"Cognitive Dimensions: From Useful
Metaphor to Engineering Truth"* — provides 12 cognitive dimensions on a
100-point budget, mapped to 5 Matrix Governance pillars.

### The 12 dimensions

Each harness is profiled across 12 dimensions:

| Dimension | Controls |
|---|---|
| Attention Granularity | Fine-grained vs coarse focus |
| Entropy Tolerance | Comfort with ambiguity |
| Causal Depth | Layers of "why" traced |
| Temporal Horizon | Past / future consideration |
| Assertion Drive | Confidence in stating conclusions |
| Reversibility Sensitivity | Weight on undoability |
| Coherence Need | Demand for internal consistency |
| Compression Instinct | Drive to simplify |
| Initiation Threshold | Evidence needed before acting |
| Completion Drive | Urgency to finish |
| Pattern Projection | Tendency to apply templates |
| Relational Awareness | Sensitivity to ripple effects |

Total budget: 100 points distributed across the 12. The constraint enforces
focus — an agent maxed on every dimension would be unfocused, not super-powered.

### The 5 pillars (engineering implementation)

Each cognitive concept maps to a real engineering lever:

| Pillar | Mechanism | What we configure |
|---|---|---|
| 1 — Input Vector | Posture anchor in system prompt | `posture_anchor` text |
| 2 — Sequential Compute | Thinking budget / effort | `effort: low \| medium \| high` |
| 3 — Sampling Variance | Temperature | `temperature: 0.0 — 1.0` |
| 4 — Logit Warping | Forbidden phrases / tool restrictions | `forbidden_phrases` list |
| 5 — Attention Masking | Context structure / abstraction level | `abstraction: detail-only \| detail-and-mid \| high` |

Pillar 1 and 2 are fully implementable in Claude Code. Pillar 3 is approximable
via prompt-level "be exploratory" / "be consistent" framing where API doesn't
expose temperature. Pillar 4 is implemented via prompt-level forbidden phrases
plus tool restriction (already done by `prescriptive-rules-block.sh`). Pillar 5
is influenced via context structure but not directly controllable.

### Starter set: 7 archetypes

| Harness | Model | Cognitive shape | Use |
|---|---|---|---|
| **Empiricist** | Sonnet | High causal_depth, coherence_need, initiation_threshold | Default for routine work; demands evidence |
| **Specifist** | Sonnet | Maxed attention_granularity, low compression_instinct | Detail review, edge-case enumeration, QA |
| **Pragmatist** | Sonnet | High completion_drive, low initiation_threshold | Move-fast prototyping, time-pressured fixes |
| **Skeptic** | Sonnet | High causal_depth + coherence_need, low assertion_drive | Adversarial review, security audits |
| **Systematist** | Sonnet | High coherence_need + completion_drive, methodical | Compliance work, structured deliverables |
| **Architect** | Opus | Maxed temporal_horizon, high relational_awareness + reversibility_sensitivity | System design, dependency-impact reviews |
| **Synthesizer** | **Opus** | Maxed pattern_projection, high compression_instinct + entropy_tolerance | Cross-domain pattern integration, synthesis steps |

**Model rule:** focused single-thread reasoning → Sonnet; cross-domain
synthesis or pattern recognition → Opus. Default team `[empiricist, specifist,
synthesizer]` costs 2× Sonnet + 1× Opus. Most routine work uses single Sonnet.
Opus reserved for genuine synthesis or architectural-level work. Cost stays
bounded.

---

## Concern lenses

Overlays applied on top of any harness. Don't replace the harness's primary
lens; augment it with a specific concern dimension.

| Lens | Concerns |
|---|---|
| **Security** | Injection, auth boundaries, secrets, privilege escalation, data exposure |
| **Performance** | Hot paths, memory, network, render cost, complexity, I/O |
| **Accessibility** | Perceivability, operability, understandability, robustness, focus management |
| **Devil's Advocate** | Strongest opposing view, failure-mode hypothesis, cost externalisation |

`Skeptic + Security` produces an adversarial security review. `Architect +
Performance` produces a structural performance review. The combinatorics
multiply usefully.

Lenses can be `default_lenses` (always-on for the project, e.g. accessibility
on UI-heavy projects) or invoked ad-hoc via dev prompt phrasing.

---

## Domain skills

Dynamically generated by `learn-codebase` per project, per major technology.
**Not templated** — bespoke per project. Two projects using Sitecore get
*different* `sitecore-knowledge` skills because their conventions, GUARD
RAILS, and CLI usage differ.

Each domain skill bundles:

- Project-specific patterns and approaches slice (relevant to the tech)
- Project-specific GUARD RAILS for the tech
- CLI references (commands actually used in this project)
- MCP references (slice of `mcp-catalogue.json` matching this tech)
- Doc-fallback rule with `official_docs_url`

Triggered by **proximity** — Claude reaches for the skill when:
- Editing files matching specific paths
- Importing distinctive modules
- The dev's prompt mentions tech keywords

### Granularity: umbrella, not fine-grained

One skill per major tech. Internal sections cover sub-concerns. Aim: 6-10
domain skills per project, not 30-50.

---

## Procedural skills

The verb-shaped skills (`update`, `deliver-work`, `audit-work`, `finding`,
`define-specialist`, `commit-clean`, `jira-context`, `tool-safety`).

These are intent-matched (Claude reaches for them based on what the dev wants
to do) rather than proximity-triggered. The harness team executes the
procedure; the domain skills auto-load to provide tech-specific context as
files are touched.

---

## Team modes

Three modes for any procedural skill invocation. Selected silently or by
keyword pattern-match.

### Single-agent (default — 99% of work)

One harness (project's `primary_harness_for_single_mode`, typically
Empiricist) executes the procedure. No lenses unless project's
`default_lenses` are always-on. Silent — no team-related output.

### Default-team (keywords: "team", "swarm", "second opinion", "multiple perspectives")

Project's `cognitive_team` harnesses execute in parallel. Each produces its
own output for each phase. A Synthesizer harness reconciles at phase
boundaries.

### Custom-team (keywords: "let me define the team", "audit with [list]")

Dev specifies harnesses + lenses + altitude overrides for this work item.

---

## Sub-agent dispatch via Claude Code's `Agent` tool

Each harness invocation maps to spawning a Claude Code sub-agent via the
`Agent` tool:

- `model` = harness's `model` field
- `prompt` = harness's `pillar_implementation.pillar_1_input_vector.posture_anchor`
  + concatenated lens overlay text
- `description` = "<harness-name> harness for <ticket-id>"

Multi-agent team mode = parallel `Agent` invocations with different harnesses.
Synthesis step (itself a Synthesizer harness) reconciles their outputs.

This aligns with how Claude Code's `Agent` tool was designed to be used.

---

## Assembly manifest schema (three-layer)

Stored in seeded `<target>/.claude/config.json.assembly`:

```json
{
  "cognitive_team": ["empiricist", "specifist", "synthesizer"],
  "domain_knowledge": ["sitecore-knowledge", "nextjs-knowledge",
                       "tailwind-radix-knowledge", "monorepo-turbo-knowledge"],
  "default_lenses": ["accessibility"],
  "primary_harness_for_single_mode": "empiricist",
  "audit_primary_harness": "skeptic",
  "altitude_band_default": "maker",
  "synthesis_harness": "synthesizer",
  "legacy_specialists": []
}
```

`learn-codebase` Step 4 proposes this; the dev approves at the human gate.

---

## Decision Quotient (deferred to v3)

The white paper defines a routing function:

`DQ = (Available Context × Capability) / (Required Context × Complexity)`

That routes which pillar combination activates per task. v2 uses **keyword
triggers** instead — simpler, immediate. v3 may add full DQ-based routing
once the keyword model is validated in real use.

---

## Altitudes (deferred to v3)

The white paper defines 5 altitude bands (Executor / Operator / Maker / Lead /
Principal) computed from Change Type, Consumption Depth, Framework
Load-Bearing, and Boundary Crossings. Each harness in v2 has a default
altitude (`altitude_default`) but altitude isn't computed task-by-task in v2
— it's a static project-level setting.

v3 may add task-level altitude computation that scales each harness's
behaviour up or down for the specific work item.

---

## Reading guide

- `harnesses/*.md` — the seven archetype profiles
- `lenses/*.md` — the four concern lens overlays
- `.claude/skills/learn-codebase/SKILL.md` — Step 4 (cognitive team proposal) and
  Step 4b (dynamic domain-skill generation)
- `procedures/deliver-work.md` — Cognitive Team Mode section
- `procedures/audit-work.md` — Step 2 (cognitive team resolution)
- `docs/architecture.md` — overall seed-and-run architecture (v1 + v2)
- The white paper (Matt Helam, "Cognitive Dimensions: From Useful Metaphor to
  Engineering Truth") — the source framework
