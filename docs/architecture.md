# Architecture

## The problem AMS solves

When working with Claude Code on a real codebase, Claude needs three kinds of
context that vanilla Claude Code doesn't reliably provide:

1. **Prescriptive rules** — what *must* and *must not* happen in this project.
   Hard rules with traceability. The codebase's lived conventions.
2. **Behavioural memory** — what's been done in this codebase before. Prior
   decisions, patterns that emerged from real work, cases that should inform
   the current task.
3. **Agent specialisation** — Claude as a frontend dev thinking about UI
   patterns is not the same as Claude as a security auditor reasoning about
   vulnerabilities. The right "voice" for the right work.

[claude-mem](https://github.com/thedotmack/claude-mem) provides the
behavioural-memory layer. It captures sessions and stores observations.
Excellent at the descriptive job.

AMS provides the **prescriptive** and **agent-specialisation** layers, plus
the connective tissue to make all three work together as one system.

---

## The statute / case-law model

A useful mental model for the layered architecture:

| Legal analogue | AMS / claude-mem layer |
|---|---|
| Constitution | `posture.md` (THINK / MINIMIZE / CUT / VERIFY — universal) |
| Statutory law | `standards/*.md` (Craft / Safety / Usability / Prose) |
| Specific statute | `patterns.md` and `approaches.md` (project-specific) |
| Black-letter enforcement | `prescriptive-rules.json` (deterministic regex/glob hard-blocks) |
| Case law | claude-mem observations (accumulated session evidence) |
| Statutory amendment | `update` skill (case-law informs proposed amendments to statute) |

**Order of consultation** is the key behaviour:

1. Posture (always)
2. Standards (per agent's standards mapping)
3. Project patterns/approaches (always within the project)
4. Claude-mem observations (when the above are silent or ambiguous)

When Claude faces a question, it consults statute first. Where statute is
silent, it consults case law. The `update` skill periodically reviews
case-law evidence and proposes amendments to statute. The dev ratifies via
human review gate. **Case law informs amendment; it does not enact amendment
unilaterally.**

---

## Seed-and-run

AMS is a build-time template source. It is *not* a runtime dependency.

When `learn-codebase` runs against a target repo, it:

1. Reads every source file (claude-mem captures observations passively).
2. Detects the stack, build/deploy strategy, patterns, approaches, and
   appropriate specialists.
3. Generates the prescriptive layer (`patterns.md`, `approaches.md`,
   `prescriptive-rules.json`, per-project `tool-safety` skill).
4. Copies the universal layer (posture, standards), the relevant specialists,
   the seeded skills (with procedure bodies inlined), the hook scripts, and
   the audit harness into the target's `.claude/` directory.
5. Excludes the seeded artifacts from cloud git via `.git/info/exclude`
   (per-clone, never committed).
6. Seeds claude-mem with synthetic init observations as common-law baseline.

After this, the target is fully self-contained:

- All hooks reference paths inside the target's `.claude/`
- All skills have their procedures inlined; no `@import` to AMS
- Universal content is copied into the target, not referenced
- AMS could be deleted from disk and the target still works

This is the core invariant. Independence test: rename AMS away mid-session;
the target's hooks and skills still function.

---

## The agent-harnessing pattern

OLD AMS organised context around three dimensions ("Trinity of Clarity":
Agent + Skill + Prompt). The new architecture preserves the principle without
the legacy name. Both `deliver-work` and `audit-work` invoke the same pattern:

1. **Read assembly manifest.** Seeded `config.json.assembly.agents` declares
   the project's agent team. Each entry: `name`, `specialist`, `standards`,
   `peer`, `environment_dependencies`.

2. **Match work intent → primary agent.** Heuristic mapping from the work
   context (ticket affected files, dev's prompt area). Surface to dev for
   confirmation; allow override.

3. **Load active agent's full context.**
   - Universal layer: posture (already in session)
   - Standards layer: agent's specific standards files
   - Specialist layer: agent's specialist file
   - Peer awareness: noted but not loaded unless invoked

4. **Surface to dev:** *"Working as `<agent>`. Standards: `<list>`.
   Peer: `<name>`."*

5. **Hand off cleanly between agents** when work spans domains. Audit-log the
   handoff.

6. **Multi-agent collaboration** for tasks needing parallel perspectives
   (e.g. security review of a frontend change).

7. **Dev override** via natural language: *"audit this from a security
   perspective"* → switches active agent.

Agent + Skill + Prompt → strongest context grounded for the work at hand.

---

## Hooks-invoke-skills

Hooks are thin orchestration. Skills hold logic. Hooks are the right place
for cheap deterministic things (probes, anchor injection, regex blocks).
Skills are the right place for reasoning (intent matching, version checks,
nuanced enforcement).

| Hook | Invokes / does |
|---|---|
| `Setup` | Probe claude-mem worker. ~10ms. No reasoning. |
| `SessionStart` | Inject prescriptive layer. Read files; emit context. |
| `UserPromptSubmit` | Lightweight anchor + mode classification. <50 tokens. |
| `PreToolUse(Bash)` | Regex-strip AI markers from git/gh. No reasoning. |
| `PreToolUse(*)` | Regex/glob match against `prescriptive-rules.json`. No reasoning. |

Skills like `tool-safety` carry the nuanced reasoning that hooks shouldn't
attempt — intent-to-command verification, version compatibility, CRUD
truthfulness analysis. Loaded conditionally by mode (`config.json.modes.<mode>.tool_safety`).

---

## Order independence

AMS hooks coexist with claude-mem's hooks (also registered globally). Claude
Code runs all matching hooks for an event in registration order, but AMS
hooks are designed to be **order-independent**:

- AMS's content is **self-anchoring** — `session-init.sh` injects framing
  ("Statute applies. Case-law via mem-search.") that holds regardless of
  whether claude-mem's context-inject ran before or after.
- AMS work that depends on claude-mem output (e.g. reconciling closed
  sessions) is deferred to the **next AMS-controlled moment** rather than
  fighting for ordering. `Stop`-style work happens at next `SessionStart`.
- This means AMS doesn't break if claude-mem's hook chain changes between
  versions. Vendor robustness.

---

## What's deliberately not in v1

- **Real-time online MCP discovery** — v2.
- **Auto-execution of canonical build/deploy commands** — v2 with sandboxing.
- **Plugin distribution** — v2.
- **Migration of existing OLD project profiles** — v1 is forward-only;
  existing profiles remain as legacy reference.
- **Behavioural distillation engine** with full claim-merging semantics —
  v1 has the framing in `update`; full implementation is iterative.
- **`Stop` and `PostToolUse` hook participation** — work moved to
  `SessionStart` and `update` for order-independence.

These deferrals are intentional. v1 ships the architecture; v2 adds
sophistication.

---

## Reading guide

- [seeding.md](seeding.md) — what `learn-codebase` actually seeds
- [migration-map.md](migration-map.md) — how OLD AMS harnesses moved to v2
- [build-deploy.md](build-deploy.md) — the build/deploy intelligence model
- [../registries/mcp-harness.md](../registries/mcp-harness.md) — MCP quality
  bar
- [../.claude/skills/learn-codebase/SKILL.md](../.claude/skills/learn-codebase/SKILL.md) —
  the engine procedure
