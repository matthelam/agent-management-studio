# Specialists — Legacy Reference (v2)

In v2 of AMS, the contents of this directory are **legacy reference material**,
not the primary agent layer.

## What changed in v2

v1 used these specialist files as agent templates — each file (e.g.
`frontend-dev.md`) defined an agent's role, standards, environment_dependencies,
and was matched to detected tech in `learn-codebase`'s Step 4.

v2 separates *cognitive style* (HOW agents think) from *domain knowledge*
(WHAT they know):

| v1 | v2 |
|---|---|
| Specialist conflated cognitive style + domain knowledge | Cognitive harness (`harnesses/`) + domain skill (dynamically generated per-project) |
| Specialist matched to tech via `specialist-catalogue.json` | Cognitive team proposed by `learn-codebase`; domain skills generated per detected tech |
| Specialist file seeded into target's `.claude/specialists/` | Harnesses seeded into `.claude/harnesses/`; domain skills generated as `.claude/skills/<tech>-knowledge/SKILL.md` |

See `docs/cognitive-architecture.md` for the v2 model.

## Why these files still exist

The `templates/specialists/*.md` files in this directory remain as:

1. **Reference material** — well-curated descriptions of common engineering
   roles and their typical concerns. Useful background reading for harness
   profile authoring or for `define-specialist` skill operations.
2. **`define-specialist` source** — when the dev runs `define-specialist`
   to add a project-specific specialist (rare in v2, kept for projects with
   specific role-tracking needs), these provide a starting point.
3. **`legacy_specialists` array** — projects can opt into v1-style specialist
   tracking via `config.json.assembly.legacy_specialists`. Specialists named
   in that array are seeded into target's `.claude/specialists/` for use
   by `define-specialist`. v2 default is empty.

## Don't add new specialists here for v2 work

For v2 work:
- New cognitive archetypes go in `harnesses/`
- New tech domain knowledge is generated dynamically by `learn-codebase`,
  not authored as templates here
- New concern overlays go in `lenses/`

Add to this directory only if:
- You're maintaining v1-compatible projects that haven't migrated
- You're adding role-tracking templates that aren't covered by the harness
  + domain skill pattern

## Files in this directory

- `_base-template.md` — used by both v1 specialist generation and v2
  `define-specialist` skill
- `frontend-dev.md`, `backend-dev.md`, `code-review.md`, `security-audit.md`,
  `accessibility-audit.md`, `storybook-dev.md`, `docker-ops.md`,
  `cms-wrapper-dev.md`, `sitecore-xmc-dev.md`, `content-author.md`,
  `content-writer.md` — 11 specialist templates (12 with base)

These remain as legacy reference. Treat as documentation of v1's role model;
v2 work should use `harnesses/` + dynamic domain skills.
