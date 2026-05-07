# Migration Map: OLD AMS → v2

Permanent record of how each key harness from the OLD AMS
(`agent-management-studio_OLD/agency/`) migrates to the v2 architecture, or is
explicitly dropped with reasoning.

Nothing was silently abandoned.

---

## Posture and Standards

| OLD | v2 | Disposition |
|---|---|---|
| `agency/posture.md` | `templates/universal/posture.md` | Migrated verbatim |
| `agency/standards/craft.md` | `templates/universal/standards/craft.md` | Migrated verbatim |
| `agency/standards/safety.md` | `templates/universal/standards/safety.md` | Migrated verbatim |
| `agency/standards/usability.md` | `templates/universal/standards/usability.md` | Migrated verbatim |
| `agency/standards/prose.md` | `templates/universal/standards/prose.md` | Migrated verbatim |

---

## Profiling engine

| OLD | v2 | Disposition |
|---|---|---|
| `agency/engines/profiling/procedures/init.md` | `.claude/skills/learn-codebase/SKILL.md` | Renamed and re-shaped (Phase 3 of plan); now an AMS-only skill that targets external repos |
| `agency/engines/profiling/procedures/rescan.md` | folded into `procedures/update.md` (preview path) | Consolidated |
| `agency/engines/profiling/procedures/update.md` | folded into `procedures/update.md` (apply path) | Consolidated |
| `agency/engines/profiling/procedures/define.md` | `procedures/define-specialist.md` | Renamed |
| `agency/engines/profiling/procedures/help.md` | — | **Dropped** — Claude's native skill discovery makes a `help` skill redundant |
| `agency/engines/profiling/diff-engine.md` | `procedures/shared/diff-engine.md` (inlined into update) | Migrated |
| `agency/engines/profiling/cascade-detection.md` | `procedures/shared/cascade-detection.md` (inlined into update) | Migrated |
| `agency/engines/profiling/stale-reference-detection.md` | `procedures/shared/stale-reference-detection.md` (inlined into update) | Migrated |
| `agency/engines/profiling/human-review-gate.md` | `procedures/shared/human-review-gate.md` | Migrated |
| `agency/engines/profiling/change-to-agent-resolution.md` | `procedures/shared/change-to-agent-resolution.md` | Migrated |
| `agency/engines/profiling/environment-snapshot-schema.md` | `docs/architecture.md` schema appendix (still TBD) + intent inlined into learn-codebase | Migrated |
| `agency/engines/profiling/environment-dependency-mapping.md` | `procedures/shared/environment-dependency-mapping.md` | Migrated |
| `agency/engines/profiling/migration-intelligence.md` | — | **Dropped in v1** — was about migrating between AMS versions; v1 is forward-only; revisit for v2 if AMS-version migration becomes a real concern |
| `agency/engines/profiling/template-decisions.md` | intent merged into `docs/architecture.md` | Migrated (intent only) |
| `agency/engines/profiling/templates/specialists/*.md` (12 files) | `templates/specialists/*.md` | Migrated verbatim (same names) |
| `agency/engines/profiling/templates/workflow.md` | `procedures/shared/workflow.md` | Migrated |
| `agency/engines/profiling/templates/profile/CLAUDE.md.template` | replaced by `learn-codebase` Step 10 seeding logic (no separate template file) | Replaced by procedural code |
| `agency/engines/profiling/templates/profile/config.json.template` | replaced by `learn-codebase` Step 10 seeding logic | Replaced by procedural code |

---

## Delivery engine

| OLD | v2 | Disposition |
|---|---|---|
| `agency/engines/delivery/procedures/work.md` | `procedures/deliver-work.md` | Migrated (full prompt guidance: 3 human gates, 5 phases, mode-specific behaviour, urgency modifier, reclassify checkpoint) |
| `agency/engines/delivery/behaviours/verifier.md` | `procedures/shared/verifier.md` | Migrated |
| `agency/engines/delivery/behaviours/resolver.md` | `procedures/shared/resolver.md` | Migrated |
| `agency/engines/delivery/behaviours/clarity/clarity-report.md` | `procedures/shared/clarity-report.md` | Migrated |
| `agency/engines/delivery/behaviours/clarity/resolution-protocol.md` | `procedures/shared/resolution-protocol.md` | Migrated |
| `agency/engines/delivery/behaviours/backlog/schemas.md` | `procedures/shared/backlog/schemas.md` | Migrated |
| `agency/engines/delivery/behaviours/backlog/lifecycle.md` | `procedures/shared/backlog/lifecycle.md` | Migrated |
| `agency/engines/delivery/behaviours/backlog/brief-population.md` | `procedures/shared/backlog/brief-population.md` | Migrated |
| `agency/engines/delivery/behaviours/backlog/elaboration.md` | `procedures/shared/backlog/elaboration.md` | Migrated |
| `agency/engines/delivery/behaviours/backlog/work-invocation.md` | `procedures/shared/backlog/work-invocation.md` | Migrated |
| `agency/engines/delivery/behaviours/backlog/completion-check.md` | `procedures/shared/backlog/completion-check.md` | Migrated |
| `agency/engines/delivery/rules.md` | `procedures/shared/delivery-rules.md` | Migrated |

---

## Investigation engine

| OLD | v2 | Disposition |
|---|---|---|
| `agency/engines/investigation/procedures/audit.md` | folded into `procedures/audit-work.md` (cross-ticket mode) | Consolidated |
| `agency/engines/investigation/procedures/trace.md` | folded into `procedures/audit-work.md` (single-ticket mode) | Consolidated |
| `agency/engines/investigation/procedures/finding.md` | `procedures/finding.md` | Migrated |
| `agency/engines/investigation/procedures/investigation.md` | parent dispatch logic at top of `procedures/audit-work.md` | Consolidated |
| `agency/engines/investigation/rules.md` | `procedures/shared/investigation-rules.md` | Migrated (referenced by audit-work and finding) |

---

## Audit logging

| OLD | v2 | Disposition |
|---|---|---|
| `agency/audit/service.md` | `templates/audit/service.md` (seeded into target's `.claude/audit/`) | Migrated |
| `agency/audit/schema.md` | `templates/audit/schema.md` | Migrated |
| `agency/audit/indexes/README.md` | `templates/audit/indexes/README.md` | Migrated |
| `agency/audit/indexes/schemas.md` | `templates/audit/indexes/schemas.md` | Migrated |

---

## Skills (`agency/.claude/skills/` in OLD)

| OLD | v2 | Disposition |
|---|---|---|
| `init/SKILL.md` | `.claude/skills/learn-codebase/SKILL.md` | Renamed; AMS-only |
| `connect/SKILL.md` | (deprecated; integration discovery folds into learn-codebase) + `templates/skills/jira-context/` (Jira specifics) | **Project-resolution role dropped** (cwd-based identity replaces it). Jira flow → `jira-context` sub-skill. Obsidian flow → **dropped entirely** |
| `define/SKILL.md` | `templates/skills/define-specialist/SKILL.md` | Renamed for natural-language clarity |
| `rescan/SKILL.md` | folded into `templates/skills/update/` (preview mode) | Consolidated |
| `update/SKILL.md` | `templates/skills/update/SKILL.md` (expanded scope) | Migrated, expanded with behavioural distillation |
| `work/SKILL.md` | `templates/skills/deliver-work/SKILL.md` | Renamed |
| `audit-work/SKILL.md` | `templates/skills/audit-work/SKILL.md` (expanded) | Migrated, consolidated with trace |
| `trace/SKILL.md` | folded into `templates/skills/audit-work/` | Consolidated |
| `finding/SKILL.md` | `templates/skills/finding/SKILL.md` | Migrated |
| `peer-review/SKILL.md` | — | **Dropped** per dev decision |
| `help/SKILL.md` | — | **Dropped** — Claude's native skill discovery makes it redundant |

---

## Project profiles

The 5 existing project profiles in `_OLD/agency/projects/`:

- `aceik-sandpit-xmc`
- `CareSuper`
- `cms-jss-apps`
- `cms-web-sitecore`
- `sitecore-blog`

**Disposition:** stay in place as legacy reference. Read-only during v2
implementation. v1 is forward-only — no automated migration.

To migrate a profile manually: run `learn-codebase` from new AMS against the
target repo. Existing seeded artifacts (if any) trigger the update-or-rebuild
prompt. v1 dev makes the call per project.

---

## Conceptual frameworks

| OLD | v2 | Disposition |
|---|---|---|
| **Trinity of Clarity** (Agent + Skill + Prompt as named principle) | Layered architecture (specialists + skills + hooks + claude-mem) | **Retired the name; preserved the principle.** Agent dimension lives in assembly manifest + specialist matching + SessionStart-loaded posture/standards. Skill dimension lives in seeded skills with inlined procedures and natural-language matching. Prompt dimension lives in UserPromptSubmit anchor + mode classification + ticket establishment + claude-mem case-law fallback. Layered architecture produces the same outcome (strongest context) without requiring the formal Trinity terminology. |

---

## New artifacts not present in OLD

These are new capabilities introduced in v2:

- `templates/skills/commit-clean/` — zero AI footprint policy enforcement
- `templates/skills/jira-context/` — extracted from connect's Jira flow + extended for runtime
- `templates/tool-safety/` — per-project CRUD-truthful tool guidance
- `templates/hooks/` (settings.json + 5 scripts) — entirely new layer (OLD had no hook system)
- `procedures/audit-logging.md` — explicit codification of how skills emit audit events (was implicit in OLD)
- `procedures/shared/` — flat shared layout (OLD inlined-or-not was inconsistent)
- `registries/tool-catalogue.json` — new (v2.2; replaces mcp-catalogue.json)
- `registries/tech-tool-map.json` — new (v2.2; replaces tech-mcp-map.json)
- `registries/skill-pack-registry.json` — new (v2.2; external skill pack source tracker)
- `registries/tool-crud-profile.json` — new
- `registries/specialist-catalogue.json` — extracted from init's matching logic
- `registries/build-deploy-signatures.json` — new (the build/deploy intelligence requirement)
- `registries/tool-harness.md` — new (v2.2; replaces mcp-harness.md; harness-strength-first evaluation)
- `.claude/skills/curate-tool/` — new AMS-side maintenance skill (v2.2; replaces curate-mcp; handles MCPs, skill packs, and agent configs)
- `docs/build-deploy.md` — new (build/deploy intelligence model)
- Build/deploy intelligence in `learn-codebase` (Step 3) — **new requirement** per user

---

## What was renamed

| OLD name | v2 name |
|---|---|
| `/init` (skill) | `learn-codebase` |
| `/work` (skill) | `deliver-work` |
| `/define` (skill) | `define-specialist` |
| `behaviours/` (delivery) | `procedures/shared/` |
| `agency/projects/<name>/` (central profile) | `<target-repo>/.claude/` (seeded into target) |
| `agency/posture.md` | `templates/universal/posture.md` (AMS source) → `<target>/.claude/posture.md` (seeded copy) |
