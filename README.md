# Agent Management Studio (AMS) v2

A build-time template source for layering AI-assisted development guidance on
top of [claude-mem](https://github.com/thedotmack/claude-mem). Each time AMS's
`learn-codebase` skill runs against a target git repository, it copies a full
self-contained set of skills, hooks, prescriptive rules, agent specialists,
and audit harness into the target's `.claude/` directory. After seeding, the
target repo is fully independent — AMS could be deleted from disk and the
target still works.

**Strict rule:** zero AI footprint in the cloud git repo. Seeded artifacts go
into `.claude/` and are excluded via `.git/info/exclude` (per-clone, never
committed) — *not* via the tracked `.gitignore`, which would itself reveal AI
involvement.

---

## Quickstart

```bash
# 1. Make sure claude-mem is installed and the worker is running
npx claude-mem install
npx claude-mem start

# 2. Clone AMS
git clone https://github.com/matthelam/agent-management-studio.git
cd agent-management-studio

# 3. Open Claude Code in the AMS directory and invoke learn-codebase against
#    a target repo:
#    "learn-codebase C:\Repositories\my-project --strict"

# 4. After learn-codebase completes, open Claude Code in the target repo.
#    SessionStart hook loads the prescriptive layer; skills are discovered
#    from .claude/skills/.

# 5. Periodically refresh the prescriptive layer based on accumulated
#    session evidence:
#    "update --preview"   (read-only)
#    "update"             (apply with human review gate)
```

---

## How it works

The architecture is a layered **statute / case-law** model:

- **Posture & Standards** (universal) — *constitutional principles*. Loaded
  every session.
- **Patterns & Approaches** (project-specific) — *statute*. Hand-curated +
  AMS-distilled prescriptive rules for this codebase.
- **prescriptive-rules.json** — *deterministic enforcement*. Hard blocks at
  PreToolUse for unmistakable violations (e.g. modifying read-only files).
- **claude-mem observations** — *case-law*. Accumulated session evidence.
  Used by `update` to propose pattern/approach amendments. Used by
  `audit-work` for investigation across work items.
- **Skills** — *procedure*. Natural-language-discoverable entry points.

Every action emits structured audit events to the project's `.claude/audit/`
log. The `audit-work` skill queries that log to reconstruct decision chains
and audit patterns.

See [docs/architecture.md](docs/architecture.md) for the full model.

---

## Repository layout

```
agent-management-studio/
├── .claude/
│   └── skills/            # AMS-only skills (Claude Code discovers these
│       │                  # when you run Claude Code inside this repo)
│       ├── learn-codebase/  # Bootstrap a target repo
│       └── curate-mcp/      # Add/refresh MCP catalogue entries
├── templates/             # Materials seeded into target repos
│   ├── skills/            # Seeded skill templates (7 skills)
│   ├── universal/         # posture.md + standards/*
│   ├── specialists/       # 12 agent specialist templates
│   ├── hooks/             # settings.json.template + scripts/
│   ├── tool-safety/       # Per-project tool-safety skill template
│   └── audit/             # Audit harness (service.md, schema.md, indexes/)
├── procedures/            # Inlined into seeded skills at seed time
│   ├── update.md
│   ├── deliver-work.md    # Full prompt guidance (3 human gates, modes, urgency)
│   ├── audit-work.md      # Single-ticket trace + cross-ticket audit consolidated
│   ├── finding.md
│   ├── define-specialist.md
│   ├── commit-clean.md    # Zero AI footprint enforcement
│   ├── jira-context.md    # Sub-skill of deliver-work
│   ├── audit-logging.md
│   └── shared/            # Pieces inlined by multiple procedures
├── registries/            # Curated source-of-truth data
│   ├── tech-mcp-map.json
│   ├── mcp-catalogue.json
│   ├── tool-crud-profile.json
│   ├── specialist-catalogue.json
│   ├── build-deploy-signatures.json
│   └── mcp-harness.md
└── docs/
    ├── architecture.md
    ├── seeding.md
    ├── migration-map.md
    └── build-deploy.md
```

---

## Skills available in target repos (after `learn-codebase`)

| Skill | Intent |
|---|---|
| `update` | Refresh prescriptive layer (env drift + claude-mem distillation). Supports `--preview`. |
| `deliver-work` | End-to-end work delivery (fix / change / upgrade). Three human gates. |
| `audit-work` | Read-only investigation (single-ticket trace OR cross-ticket pattern audit). |
| `finding` | Capture a structured finding with severity + recommendation. |
| `define-specialist` | Add/refine/promote a project specialist. |
| `commit-clean` | Strip AI markers from git commits/PRs/comments. Skill + hook pair. |
| `jira-context` | Sub-skill of `deliver-work`; loads Jira ticket context. |
| `tool-safety` | Per-project; CRUD-truthful tool guidance. |

Skills are discovered by Claude Code based on natural-language descriptions —
the dev doesn't type slash-commands; they describe intent.

---

## Hooks installed in target repos

| Event | Script | Purpose |
|---|---|---|
| `Setup` | `setup-probe.sh` | Probe claude-mem worker reachable; surface remediation if not |
| `SessionStart` | `session-init.sh` | Inject prescriptive layer; reconcile prior sessions |
| `UserPromptSubmit` | `prompt-anchor.sh` | Lightweight per-prompt anchor + mode classification |
| `PreToolUse(Bash)` | `commit-clean-pre-bash.sh` | Strip AI markers from git/gh commands |
| `PreToolUse(*)` | `prescriptive-rules-block.sh` | Hard-block tool calls violating prescriptive rules |

All hooks register from `.claude/settings.json` (seeded by `learn-codebase`).
None reference back to AMS paths — target is fully independent.

---

## What this isn't

- **Not a Claude Code plugin** — AMS is a git repo cloned per-machine. Plugin
  distribution is a v2 consideration.
- **Not a runtime dependency** — once `learn-codebase` has seeded a target,
  AMS can be deleted and the target still works.
- **Not real-time MCP discovery** — v1 ships a curated registry; ecosystem
  discovery happens against that registry. Real-time online discovery for
  unknown tech is v2.
- **Not an automatic build/deploy executor** — v1 surfaces canonical commands
  and recommends manual verification. Sandboxed auto-execution is v2.

---

## License

See LICENSE.

---

## Documentation

- [Architecture](docs/architecture.md) — The seed-and-run model, statute vs
  case-law, agent-harnessing pattern
- [**Cognitive Architecture (v2)**](docs/cognitive-architecture.md) — How v2
  separates cognitive harnesses, concern lenses, and domain skills. The
  three-layer model
- [Seeding](docs/seeding.md) — What gets seeded into target repos and how
- [Migration map](docs/migration-map.md) — How OLD AMS harnesses migrated to
  v2
- [Build & deploy intelligence](docs/build-deploy.md) — How `learn-codebase`
  identifies canonical build/deploy commands
- [MCP quality harness](registries/mcp-harness.md) — Bar for adding MCPs to
  the curated registry

## v2 directories at a glance

- `harnesses/` — 7 cognitive archetype profiles (Empiricist, Specifist,
  Pragmatist, Skeptic, Systematist, Architect, Synthesizer)
- `lenses/` — 4 concern lens overlays (Security, Performance, Accessibility,
  Devil's-Advocate)
- `templates/specialists/` — **legacy reference** (v1 model); v2 uses
  harnesses + dynamic domain skills
