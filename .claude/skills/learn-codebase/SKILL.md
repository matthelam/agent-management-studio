---
name: learn-codebase
description: Bootstrap or rebuild the AMS profile for a target git repository. Scans the codebase, detects the stack, identifies build & deploy commands (documentation-first then code-second), proposes the agent team with full specialist definitions, builds the assembly manifest, generates patterns.md / approaches.md / prescriptive-rules.json / per-project tool-safety skill, then seeds everything into the target repo's .claude/ directory (excluded from cloud git via .git/info/exclude). Use when starting AMS on a fresh repo, or to rebuild a profile from scratch.
---

# learn-codebase

AMS-only skill. Run from inside `C:\Repositories\agent-management-studio` (or
wherever AMS is checked out). Targets another git repo by absolute path.

After this skill completes, the target repo is fully self-contained — AMS could
be deleted from disk and the target's hooks/skills/prescriptive layer would
still function.

---

## Invocation

```
learn-codebase <absolute-path-to-target-repo> [--strict] [--reconfigure-integrations]
```

- `--strict` — produce strict-mode prescriptive layer (GUARD RAILS, hard rules).
  Default mode produces descriptive patterns; strict produces deterministic
  rules that drive `prescriptive-rules.json`. Strict mode is recommended for
  production projects.
- `--reconfigure-integrations` — re-run only the Jira (and any future
  integration) discovery without re-doing the full scan. Useful when changing
  Jira projects without rebuilding the profile.

---

## Run logging (mandatory, threads through every step)

**Every learn-codebase invocation produces a structured run log** written to
`<ams-root>/logs/learn-codebase-<iso-timestamp>-<run-id>.jsonl`. Schema and
helper definitions are in `procedures/ams-audit-logging.md`.

### At invocation start (before Step 0)

1. Generate a UUIDv4 as `RUN_ID`.
2. Resolve `AMS_HOME` (the path to this AMS checkout — typically the cwd when
   the skill is invoked).
3. Compute `LOG_FILE=$AMS_HOME/logs/learn-codebase-$(date -u +%Y-%m-%dT%H-%M-%S)-$RUN_ID.jsonl`.
4. Ensure `$AMS_HOME/logs/` exists.
5. Define the `emit_event` bash helper per `procedures/ams-audit-logging.md`.
6. Emit `invocation_start` with payload:
   ```json
   { "args": ["<target-path>", "--strict|--reconfigure-integrations|..."],
     "cwd": "<cwd>", "ams_version": "v2.1", "target": "<absolute target path>",
     "run_log": "<LOG_FILE absolute path>" }
   ```
7. Emit `claude_mem_project_id_resolved` immediately after probing
   claude-mem health (Step 0): payload `{ "auto_detected_id": "<from cwd>",
   "target_basename": "<basename of target path>", "id_will_be_used":
   "<which id learn-codebase will tag synthetic observations with>",
   "reason": "..." }`. **This event surfaces project-ID misroute risk at run start.**

### At each Step boundary

Emit `step_start` (with `step_id` matching the step number, `step_name`
matching the heading) before doing the step's work; emit `step_end` after,
with `outcome: "success" | "failure" | "skipped"` and `duration_ms`.

### At each substantive event within a step

Use the event taxonomy in `procedures/ams-audit-logging.md`:

| When | Emit |
|---|---|
| Probing claude-mem / Bun / a CLI / an MCP | `dependency_probe` (and `dependency_remediation` if action taken) |
| Writing any file to target's `.claude/` | `artifact_write` with path, bytes, sha256 |
| Skipping a planned write | `artifact_skip` with reason |
| Step 4 — proposing the cognitive team | `cognitive_team_proposed` then (after dev review) `cognitive_team_approved` |
| Step 4b — generating each domain skill | `domain_skill_generated` per tech |
| Step 6 — pattern detected | `pattern_detected` |
| Step 7 — approach detected | `approach_detected` |
| Step 8 — prescriptive rule generated | `prescriptive_rule_generated` |
| Step 11 — `.git/info/exclude` write | `gitignore_update` with `entries_added` |
| Step 12 — synthetic observation seeded | `claude_mem_observation_seeded` per observation |
| Any human review point | `human_gate` |
| Any non-fatal anomaly | `warn` |
| Any fatal failure | `error` (with the original exception detail) |

### At invocation end

Emit `invocation_end` with:
```json
{ "outcome": "success" | "failure" | "stopped",
  "duration_ms": <total>,
  "summary": {
    "steps_completed": <n>, "steps_skipped": <n>,
    "artifacts_written": <n>, "patterns_detected": <n>,
    "approaches_detected": <n>, "guard_rails_extracted": <n>,
    "prescriptive_rules_generated": <n>,
    "synthetic_observations_seeded": <n>,
    "claude_mem_project_id_used": "<id>"
  }
}
```

### Error path

On any unhandled error, emit `error` with full context, then `invocation_end`
with `outcome: "failure"`. **Never let an exception propagate without a
matching log entry** — that's the failure mode the smoke test surfaced
(silent stalling).

### Log retention

At invocation start, prune `$AMS_HOME/logs/learn-codebase-*.jsonl` files older
than 7 days OR beyond the most-recent 50 (whichever keeps more), per
`procedures/ams-audit-logging.md`.

---

## Step 0 — Preflight

Emit `step_start` with `step_id: "0"`, `step_name: "preflight"`.

Each probe below emits a `dependency_probe` event with `dependency`,
`outcome`, `details`. **Any failed hard probe halts execution**: emit
`error`, `invocation_end` with `outcome: "failure"`, and stop. Do NOT
proceed with a partial seed — that's the failure mode the smoke test exposed.

1. **Hard: claude-mem worker reachable.** `curl -sf --max-time 5
   http://127.0.0.1:37777/api/health`. (Note: 5-second timeout, not 2 — worker
   under load may take longer to respond.) On unreachable:
   - Emit `dependency_probe` with `outcome: "unreachable"` and the
     remediation hint `npx claude-mem start`.
   - Emit `error` and stop. **Do NOT continue.** This is the issue-4 fix —
     learn-codebase REQUIRES claude-mem; soft-fail is wrong here.
2. **Hard: Bun installed.** `bun --version`. On missing: emit `error` and stop.
3. **Hard: target path is a git repo.** Verify directory exists and contains
   `.git/`. On failure: emit `error` and stop.
4. **Resolve and log claude-mem project IDs (the v2.1 fix for issue 2).**
   - Probe claude-mem's project resolution from this cwd: hit `/api/search`
     with a no-op query and inspect what project tag it returns, OR read
     `~/.claude-mem/observer-sessions/` for the most recent session's
     project field.
   - Compute `target_basename = basename(<target-path>)` (e.g.
     `aceik-sandpit-xmc`).
   - Decide which project ID to use for synthetic observations in Step 12 —
     **always `target_basename`**, never the auto-detected AMS-side ID.
   - Emit `claude_mem_project_id_resolved` with full payload as defined in
     the Run logging section.
5. **`cd` into target before any further work.** This is the v2.1 fix for the
   project-ID misroute: by changing cwd into the target before the file sweep,
   claude-mem's auto-detection picks up the target's basename. (If `cd`
   into target is impractical for the AMS skill execution model, alternative:
   set `CLAUDE_MEM_SKIP_TOOLS += Read` for the sweep duration and emit one
   bulk synthetic observation in Step 12 with explicit `project: "<target_basename>"`.)
6. **Check for existing seed.** If `<target>/.claude/config.json` exists with
   `environment_snapshot`, route to update-or-rebuild prompt:
   - **(a) Update** — invoke `update` skill in the target instead of full
     rebuild. Preserves existing assembly + manual edits.
   - **(b) Full rebuild** — proceed with this procedure. Warn that existing
     prescriptive artifacts will be replaced.
   - Emit `human_gate` with the decision.

Emit `step_end` for Step 0 before proceeding.

### Step 0.5 — Early gitignore protection (the v2.1 fix for issue 1)

**Move the `.git/info/exclude` write to here, before any file is seeded.**

Originally Step 11; promoted to Step 0.5 because partial-failure scenarios
must not leave a window where seeded `.claude/` files are git-visible.

1. Append `.claude/` (or finer-grained subdirs per
   `assembly.gitignore_granularity` if set) to
   `<target>/.git/info/exclude`. Idempotent — check for existing entry first.
2. Emit `gitignore_update` with `target`, `entries_added`,
   `entries_already_present`.
3. **NEVER touch the tracked `.gitignore`.** That's the no-AI-footprint rule.

If this step fails (permissions, not a git repo, etc.): emit `error` and stop.
The seed must not proceed if the protection layer can't be established.

---

## Step 1 — File sweep (one pass, both outputs)

AMS reads every source file in the target. Each Read fires claude-mem's
`PreToolUse(Read)` and `PostToolUse(*)` hooks; observations are captured
passively. **Do NOT separately invoke claude-mem's `learn-codebase` skill** —
that would be a redundant second sweep.

For repos with thousands of source files, consider temporarily appending
`Read` to `CLAUDE_MEM_SKIP_TOOLS` in `~/.claude-mem/settings.json` for the
sweep duration, then emit a single bulk synthetic observation at the end. (For
v1, observe the cost during a real sweep before deciding whether this
mitigation is necessary.)

Files to read:
- All source files (by extension, language-aware)
- All `package.json`, `*.csproj`, `*.sln`, `pom.xml`, `build.gradle`,
  `requirements.txt`, `pyproject.toml`, `Cargo.toml`, `go.mod`
- All config files: `tsconfig.json`, `.eslintrc*`, `.prettierrc*`,
  `tailwind.config.*`, `next.config.*`, `nuxt.config.*`, `vite.config.*`,
  `webpack.config.*`, `jest.config.*`, `vitest.config.*`
- `Dockerfile*`, `docker-compose*`, `compose.yaml`
- `turbo.json`, `nx.json`, `lerna.json`, `pnpm-workspace.yaml`
- `sitecore.json`, `*.scproj`, TDS / Unicorn / SCS configs
- CI/CD: `.github/workflows/*`, `azure-pipelines*`, `.gitlab-ci.yml`,
  `Jenkinsfile`, `bitbucket-pipelines.yml`
- Documentation: `README.md`, `CONTRIBUTING.md`, `docs/**/*.md`,
  `BUILD.md`, `DEPLOY.md`, `DEPLOYMENT.md`, `SETUP.md`, `INSTALL.md`,
  `AGENT.md`, `agent-instructions.md`

---

## Step 2 — Stack detection

Produce structured `environment_snapshot`:
- `runtime` — Node version, Python version, .NET version, etc.
- `package_manager` — npm/pnpm/yarn/poetry/nuget version
- `frameworks` — primary frameworks with exact versions
- `testing` — test runners, e2e tools, visual regression
- `linting` — ESLint, Prettier, etc.
- `key_dependencies` — significant libraries (state, styling, validation)
- `structure` — monorepo vs single-app, src layout, package directories
- `content_hashes` — SHA-256 of patterns.md and approaches.md (initially
  `pending-first-write`)

**Human gate:** present scan results to dev. Confirm detected stack is correct.
Allow corrections.

---

## Step 3 — Build/deploy intelligence

Solves the requirement: *"the skill needs to learn and have tested a very key
element. How to build the solution and how to deploy the solution."*

### Documentation-first

Read `README.md`, `CONTRIBUTING.md`, `BUILD.md`, `DEPLOY.md`, etc. (already
read in Step 1; analyse now). Extract any documented build/test/deploy commands
verbatim with their location.

### Code-second

Inspect:
- `package.json` `scripts` section — which scripts are canonical?
- Makefile / Taskfile.yml / justfile — top-level targets
- `*.csproj` / `*.sln` — MSBuild targets
- `Dockerfile` / `docker-compose.yml` — container build steps
- `turbo.json` / `nx.json` — pipeline definitions
- `sitecore.json` / Sitecore CLI configs / TDS / Unicorn — content
  serialization commands
- CI/CD pipeline files — what does CI actually run for build/test/deploy?

### Solution-type classification

Match against `registries/build-deploy-signatures.json`:

- **headless** — Next.js / Nuxt / SvelteKit / etc.; deploy to Vercel /
  Netlify / Cloudflare Pages / etc.
- **dotnet** — .csproj/.sln present; build via dotnet/MSBuild; deploy varies
- **sitecore-xmc** — `sitecore.json` + `*.scproj` + TDS/Unicorn signals;
  Sitecore CLI; container dev environment; content-sync separate from code
  build
- **sitecore-jss** — Sitecore JSS app (mix of headless + Sitecore content)
- **hybrid-sitecore-content-sdk** — Next.js + Sitecore Content SDK
- **other** — fallback; surface signature for human classification

### Synthesis — one canonical command per concern

Reconcile docs vs code. Conflicts are common (docs outdated, code incomplete).
Surface conflicts to the dev. Produce:
- `canonical_build` (e.g. `pnpm turbo run build`)
- `canonical_test` (e.g. `pnpm turbo run test`)
- `canonical_deploy` (when applicable in dev workflow)
- `canonical_content_sync` (Sitecore-style only)
- `prerequisites` — env vars, services, credentials needed

Write to seeded `.claude/build-deploy.md` and into
`config.json.environment_snapshot.build_deploy`.

### v1: do NOT auto-execute

Surface canonical commands; recommend dev verifies manually. Auto-execution
in a sandbox is v2.

---

## Step 4 — Cognitive team proposal (v2)

Cognitive harnesses are HOW agents think; domain skills (Step 4b) are WHAT
they know. This step decides the team shape; Step 4b generates the per-tech
domain knowledge.

### Default-team proposal heuristics

Based on stack signals + project shape, propose a default cognitive team for
this project. Heuristics:

| Project signal | Suggested default team | Reason |
|---|---|---|
| UI-heavy (React + Tailwind/Radix + Storybook) | `[empiricist, specifist, synthesizer]` + accessibility lens | Specifist for UI detail; synthesizer to integrate UI patterns; accessibility always-on |
| Sitecore + accelerator + monorepo | `[architect, empiricist, specifist, synthesizer]` | Architect for cross-package boundaries; specifist for Sitecore wrapper edge cases |
| .NET backend | `[skeptic, empiricist, architect]` + security lens | Backend services need adversarial security review; architect for API boundary design |
| Greenfield prototype | `[pragmatist, synthesizer]` | Move fast; synthesize early patterns |
| Compliance-heavy / regulated | `[systematist, skeptic, empiricist]` + security lens + devils-advocate lens | Process completeness + adversarial check |

Adjust per detected solution-type and any human-supplied hints.

### Primary harness for single-mode

The single-agent default for routine work. Typically `empiricist` unless the
project has a distinctive shape:

| Project shape | primary_harness_for_single_mode |
|---|---|
| (default) | `empiricist` |
| Compliance-heavy | `systematist` |
| Prototype-heavy | `pragmatist` |
| Architectural-decision-heavy | `architect` *(but expensive — Opus)* |

For most projects: `empiricist`.

### Audit primary harness (optional override)

Some projects benefit from a non-default harness for `audit-work` single
mode:

| Project shape | audit_primary_harness |
|---|---|
| (default — same as primary) | `empiricist` |
| Security-sensitive | `skeptic` |
| Architecture-debt-heavy | `architect` |

### Default lenses

Always-on lenses for this project:

| Project signal | default_lenses |
|---|---|
| UI-heavy / consumer-facing | `[accessibility]` |
| Security-sensitive (auth, payments, PII) | `[security]` |
| Performance-critical (real-time, render-heavy) | `[performance]` |

Multiple lenses can apply.

### Human review gate

Surface the proposed team to the dev:

```
COGNITIVE TEAM PROPOSAL — <project-name>

Default team (engaged when "team" / "swarm" / "second opinion" mentioned):
  - empiricist     (Sonnet)
  - specifist      (Sonnet)
  - synthesizer    (Opus)

Single-agent default (engaged silently for routine work):
  - empiricist (Sonnet)

Audit-work single default:
  - skeptic (Sonnet) — adversarial baseline for audits

Default lenses (always-on):
  - accessibility

Approve, modify, or override?
```

Dev can: accept / modify (swap harnesses, lenses) / specify per-altitude
overrides.

---

## Step 4b — Dynamic domain-skill generation (v2)

For each detected major technology, **generate a project-specific domain
skill** with proximity triggers. **No templating** — the skill is bespoke
to this project.

### Per-tech generation

For each tech detected (Sitecore, Next.js, Tailwind+Radix, Turborepo, etc.):

1. **Pull the registry slice:**
   - From `registries/tech-mcp-map.json`: MCPs, CLIs, specialists,
     `official_docs_url`
   - From `registries/mcp-catalogue.json`: detailed MCP metadata for any
     MCPs in the slice
   - From `registries/tool-crud-profile.json`: CRUD-truthfulness for the
     slice's tools

2. **Extract the project-specific slice from analysis:**
   - GUARD RAILS in `approaches.md` mentioning this tech
   - Patterns in `patterns.md` mentioning this tech
   - CLI commands actually used in this project (from CI configs, scripts,
     dev workflow docs)
   - File patterns / paths where this tech is in use

3. **Generate the domain skill body:**

```markdown
---
name: <tech>-knowledge
description: |
  Use when working in <file-patterns>, when editing files that import
  <tech-imports>, or when the user mentions <tech-keywords>.
  Provides <project-name>'s specific patterns, conventions, GUARD RAILS,
  CLI references, MCP methods, and doc fallback for <tech>.
---

# <tech> in <project-name>

## Project-specific patterns
<extracted slice of patterns.md for this tech>

## Project-specific approaches & GUARD RAILS
<extracted slice of approaches.md for this tech>

## CLI commands used in this project
<canonical commands from build-deploy.md slice + project-specific usage>

## MCP methods (when applicable)
<curated list from mcp-catalogue with concrete invocation examples>

## Doc fallback
If uncertain about implementation, search the official documentation at
<official_docs_url> before improvising. For version-specific behaviour,
include the version (this project uses <version>) in your search.
```

4. **Write to seeded `.claude/skills/<tech>-knowledge/SKILL.md`.**

### Granularity: umbrella, not fine-grained

One domain skill per major tech, not per sub-concern. Internal sections
cover sub-concerns (e.g. `sitecore-knowledge` covers content-sync, wrappers,
JSS, CLI usage all together — Claude reads relevant sections based on
proximity). Aim: 6-10 domain skills per project, not 30-50.

### Proximity triggers

The skill's `description` field is the proximity trigger. It should mention:
- Specific file path patterns (e.g. `packages/ui-sitecore/**/*.tsx`)
- Distinctive imports (e.g. `@sitecore-content-sdk/*`)
- Technology keywords likely in dev prompts

Description tightness matters — a vague description ("Use when working with
Next.js") triggers too eagerly across unrelated work; a specific description
("Use when editing files in apps/xmc-shadcn or files importing
@sitecore-jss/*") triggers correctly.

### Each domain skill is the complete legal system for its tech

Self-contained: bundles patterns + approaches slice + GUARD RAILS + tools
+ doc-fallback in one place. No `@import` to other files in the seeded
target. Independence is preserved.

---

## Step 5 — Assembly manifest construction (v2 three-layer schema)

Build the assembly manifest with three separated layers:

```json
{
  "project": "<project-name>",
  "assembly": {
    "cognitive_team": ["empiricist", "specifist", "synthesizer"],
    "domain_knowledge": ["sitecore-knowledge", "nextjs-knowledge",
                         "tailwind-radix-knowledge", "monorepo-turbo-knowledge"],
    "default_lenses": ["accessibility"],
    "primary_harness_for_single_mode": "empiricist",
    "audit_primary_harness": "skeptic",
    "altitude_band_default": "maker",
    "synthesis_harness": "synthesizer"
  }
}
```

Write into seeded `config.json.assembly`. The harness names reference
seeded `.claude/harnesses/<name>.md`. The domain_knowledge names reference
generated `.claude/skills/<name>/SKILL.md`. The lens names reference
seeded `.claude/lenses/<name>.md`.

**Legacy specialist mapping:** if the project benefits from explicit domain
specialist documentation (e.g., for `define-specialist` skill to refine), a
secondary `legacy_specialists` array can be populated with names from
`templates/specialists/`. These are reference material, not the primary
agent layer in v2.

---

## Step 6 — Pattern detection

Scan codebase for recurring coding patterns. Default mode produces descriptive
patterns; `--strict` produces hard rules.

@procedures/shared/diff-engine.md *(used for pattern recognition signals)*

Categories to scan: state management, data fetching, error handling, file
organization, naming conventions, test patterns, component patterns, API
patterns, CMS wrapper patterns (Sitecore-aware), deployment patterns.

**Strict mode output format** (each rule):
```
RULE: <constraint>
DO <permitted action> ONLY when <condition>
DO NOT <prohibited action>
RATIONALE: <evidence: file paths with line numbers, counts>
EXAMPLE (correct): <code snippet>
EXAMPLE (wrong): <code snippet>
```

Write to seeded `.claude/patterns.md`.

---

## Step 7 — Approach detection

Scan for architectural approaches. Default produces descriptive; `--strict`
produces APPROACH/BOUNDARY/RATIONALE/GUARD RAILS.

Categories: authentication, database access, deployment, environment config,
logging, monitoring, content serialization (Sitecore), CMS wrapper strategy,
multi-package boundaries.

**Strict mode output format**:
```
APPROACH: <what is used and where>
BOUNDARY:
  DO <permitted actions>
  DO NOT <prohibited actions>
RATIONALE: <human context + evidence>
GUARD RAILS:
  - <file path or resource> — <constraint>
```

Write to seeded `.claude/approaches.md`.

GUARD RAILS specifically must be machine-parseable into
`prescriptive-rules.json` in the next step.

---

## Step 8 — Generate `prescriptive-rules.json`

Parse GUARD RAILS sections from `approaches.md`. For each guard rail:

```
- packages/ui/src/styles/theme-1.css — READ ONLY for all agents
```

Emit a rule:

```json
{
  "id": "theme-tokens-readonly",
  "tools": ["Edit", "Write"],
  "match": {"path_glob": "packages/ui/src/styles/theme-*.css"},
  "action": "block",
  "reason": "GUARD RAIL: theme-1.css is READ ONLY for all agents. Reserved for humans. See approaches.md."
}
```

The parser must handle:
- File path patterns (glob → regex)
- Bash command patterns (regex)
- Multi-file rules (cross-package boundaries)

Write to seeded `.claude/prescriptive-rules.json`. The `prescriptive-rules-block.sh`
hook reads this file at runtime.

*(Implementation note: parser schema is a collaborative design item. v1 may
start with a hand-curated subset and expand parser coverage iteratively.)*

---

## Step 9 — Generate per-project `tool-safety` skill

Read `templates/tool-safety/SKILL.md.template`. Substitute:
- `{{PROJECT_NAME}}` — target's name
- `{{TIMESTAMP}}` — ISO-8601 now
- `{{TOOL_PROFILE_VERSION}}` — version of `tool-crud-profile.json`
- `{{TECH_MAP_VERSION}}` — version of `tech-mcp-map.json`
- `{{TOOL_CRUD_TABLE}}` — markdown table of CRUD profiles for tools matched
  to this project's stack (from `tool-crud-profile.json`)
- `{{VERSION_CHECKS}}` — version-check commands for tools in stack
- `{{SCOPED_ACCESS_TABLE}}` — mirror of GUARD RAILS in lookup form

Write to seeded `.claude/skills/tool-safety/SKILL.md`.

---

## Step 10 — Seed everything into target's `.claude/` (v2 layout)

Create `<target>/.claude/` and populate:

```
.claude/
├── settings.json                # from templates/hooks/settings.json.template
├── hooks/
│   └── scripts/
│       ├── setup-probe.sh
│       ├── session-init.sh
│       ├── prompt-anchor.sh
│       ├── commit-clean-pre-bash.sh
│       └── prescriptive-rules-block.sh
├── harnesses/                   # v2: cognitive harnesses (the "team")
│   ├── empiricist.md            # verbatim from harnesses/
│   ├── specifist.md
│   ├── synthesizer.md
│   └── ...                      # only those listed in assembly.cognitive_team
│                                # plus primary_harness_for_single_mode
│                                # plus audit_primary_harness
├── lenses/                      # v2: concern lens overlays
│   ├── accessibility-lens.md    # verbatim from lenses/
│   └── ...                      # only those in default_lenses + the four standard ones
├── posture.md                   # verbatim from templates/universal/
├── standards/
│   ├── craft.md
│   ├── safety.md
│   ├── usability.md
│   └── prose.md
├── specialists/                 # legacy reference; only if assembly.legacy_specialists set
├── skills/
│   ├── update/SKILL.md                       # procedures/update.md inlined
│   ├── deliver-work/SKILL.md                 # procedures/deliver-work.md inlined
│   ├── audit-work/SKILL.md                   # procedures/audit-work.md inlined
│   ├── finding/SKILL.md
│   ├── define-specialist/SKILL.md
│   ├── commit-clean/SKILL.md
│   ├── jira-context/SKILL.md
│   ├── tool-safety/SKILL.md                  # generated per-project
│   ├── sitecore-knowledge/SKILL.md           # v2: dynamically generated per-tech
│   ├── nextjs-knowledge/SKILL.md             # v2: dynamically generated per-tech
│   ├── tailwind-radix-knowledge/SKILL.md     # v2: dynamically generated per-tech
│   └── ...                                   # one per major tech detected
├── audit/
│   ├── service.md
│   ├── schema.md
│   └── indexes/
│       ├── README.md
│       └── schemas.md
├── patterns.md                  # generated this run
├── approaches.md                # generated this run
├── config.json                  # generated this run (v2 three-layer assembly)
├── prescriptive-rules.json      # generated this run
└── build-deploy.md              # generated this run
```

### Procedural skill seeding (no change from v1)

For each `templates/skills/<name>/SKILL.md` (the procedural skills — update,
deliver-work, audit-work, etc.):
1. Read the template (frontmatter + `{{INLINE: procedures/<name>.md}}`).
2. Resolve `{{INLINE: ...}}` by reading the procedure file from AMS.
3. Recursively resolve `@procedures/shared/<file>.md` references inside.
4. Write fully-resolved SKILL.md to target.

### v2 — Harness seeding

For each harness in the resolved team (cognitive_team + primary_for_single_mode +
audit_primary_harness):
1. Read `harnesses/<name>.md` from AMS.
2. Copy verbatim to target's `.claude/harnesses/<name>.md`.

Don't seed harnesses not in the project's team — only those the dev approved.
The dev can `define-specialist` later to add more.

### v2 — Lens seeding

Seed all four standard lenses (security, performance, accessibility,
devils-advocate) so they're available for ad-hoc invocation. Mark which are
always-on per `assembly.default_lenses`. Verbatim copies from AMS `lenses/`.

### v2 — Domain-skill seeding (dynamic, no template)

For each tech detected in Step 4b, **the generated domain-skill body** has
already been produced. Write directly to target's
`.claude/skills/<tech>-knowledge/SKILL.md`. No inlining step — the body is
already self-contained.

After this full step, the target has:
- Procedural skills (verb-shaped, intent-matched)
- Domain skills (noun-shaped, proximity-triggered)
- Cognitive harnesses (HOW-shaped, dispatched via Agent tool)
- Concern lenses (overlay-shaped, applied on top of harnesses)
- Universal content (posture + standards)
- Hook scripts + audit harness

**Independence preserved:** zero references back to AMS paths. Rename-AMS
test still passes.

Make hook scripts executable: `chmod +x .claude/hooks/scripts/*.sh`.

---

## Step 11 — Append to `.git/info/exclude`

**NEVER touch the tracked `.gitignore`.** Append to `<target>/.git/info/exclude`
(per-clone, never committed):

```
# AMS-managed (do not commit)
.claude/
```

If `.git/info/exclude` already has a `.claude/` entry: leave it alone.
If `.gitignore` already has `.claude/` (project's existing convention):
surface to dev — they may have intentionally chosen to commit `.claude/`
configurations; in which case, fall back to `.git/info/exclude` for the
AMS-specific subdirs only and warn that mixing tracked/untracked `.claude/`
content is fragile.

---

## Step 12 — Seed claude-mem with synthetic init observations

For each detected pattern/approach/build-step/specialist-decision, emit a
synthetic observation into claude-mem:

```bash
curl -X POST http://127.0.0.1:37777/api/observations \
  -H 'Content-Type: application/json' \
  -d '{
    "type": "init-discovery",
    "project": "<target-name>",
    "title": "Project uses CVA for component variants",
    "narrative": "Detected via grep: 47 component files import cva from class-variance-authority...",
    "concepts": ["cva", "variants", "components"],
    "files_read": ["packages/ui/src/components/Button.tsx", "..."]
  }'
```

This gives `update`'s behavioural-distillation step a baseline to compare
against. The init evidence becomes "common law" baseline that future session
observations can confirm or contradict.

*(Implementation note: claude-mem's observation-injection API is referenced
abstractly here. Confirm the exact endpoint shape during implementation
against claude-mem's worker source.)*

---

## Step 13 — Audit-log the init

Emit `learn_codebase_completed` event via the seeded audit service (now active
in the target):

```json
{
  "type": "learn_codebase_completed",
  "actor": "system",
  "payload": {
    "target_path": "<absolute path>",
    "stack_summary": {...},
    "agents_proposed": [...],
    "agents_generated": [...],
    "patterns_detected": <n>,
    "approaches_detected": <n>,
    "guard_rails_extracted": <n>,
    "synthetic_observations_seeded": <n>,
    "duration_seconds": <n>
  }
}
```

---

## Step 14 — Final report

Surface to dev:

```
LEARN-CODEBASE COMPLETE
  Target:         <absolute path>
  Profile:        <target>/.claude/
  Stack:          <summary>
  Agents:         <count>  (curated: <n>, generated: <n>)
  Patterns:       <count>
  Approaches:     <count>
  GUARD RAILS:    <count> → <count> deterministic rules
  Build:          <canonical-build-command>
  Deploy:         <canonical-deploy-command or N/A>
  .git/info/exclude updated.   .gitignore unchanged.
  Synthetic observations seeded into claude-mem.

Next steps:
  - Open a Claude Code session in <target>/. SessionStart will load the prescriptive layer.
  - Run `update --preview` periodically to see proposed refreshes.
  - For Jira-tracked work: invoke `deliver-work` and let it call `jira-context`.
```

---

## Failure handling

| Failure | Action |
|---|---|
| claude-mem worker unreachable | Stop at Step 0; remediation surfaced |
| Target path doesn't exist | Stop at Step 0 |
| Existing config detected | Route to update-or-rebuild prompt |
| Stack detection ambiguous | Surface to dev; allow correction |
| Generated specialist rejected by dev | Drop from team; continue without it |
| GUARD RAILS parse failure | Skip rule; log parse error to `audit/errors.jsonl`; surface unparsed entries to dev |
| Synthetic observation seed fails | Continue; log to `audit/errors.jsonl`; warn dev that update's baseline will be missing |
| `.git/info/exclude` write fails (permissions) | Surface; ask dev to add manually |

---

## Idempotence

`learn-codebase` on a target with existing config offers update-vs-rebuild.
On rebuild, all generated artifacts are overwritten. Hand-edited
`patterns.md`/`approaches.md` content should be preserved when possible (use
`<claude-mem-context>`-style wrappers for AMS-generated content blocks vs
human-authored). v1 will warn before overwriting any file containing
human-authored sections.
