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

## Step 0 — Preflight

1. **Verify claude-mem worker reachable.** `curl -sf
   http://127.0.0.1:37777/api/health`. If unreachable: surface remediation
   (`npx claude-mem start`) and stop.
2. **Verify Bun installed.** Required by claude-mem; check via `bun --version`.
3. **Verify target path exists** and is a directory containing a `.git/`
   subdirectory.
4. **Check for existing seed.** If `<target>/.claude/config.json` exists with
   `environment_snapshot`, route to update-or-rebuild prompt:
   - **(a) Update** — invoke `update` skill in the target instead of full
     rebuild. Preserves existing assembly + manual edits.
   - **(b) Full rebuild** — proceed with this procedure. Warn that existing
     prescriptive artifacts will be replaced.

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

## Step 4 — Specialist matching & agent-definition proposal

1. Match detected technologies against `templates/specialists/` and
   `registries/specialist-catalogue.json`.
2. **Curated tech** — select the existing specialist; no new definition.
3. **Uncovered tech** — generate candidate from
   `templates/specialists/_base-template.md`, populating identity,
   version-conditional rules, scope, standards refs, peer pairing,
   environment_dependencies from scan data. Mark `generated: true`.
4. **Human review gate** — surface proposed agent team:
   - For curated specialists: name + standards + peer + env_deps
   - For generated specialists: full markdown definition (dev can read +
     refine inline)
   - Per-agent dev action: accept / modify / reject
5. Generated specialists that the dev refines and accepts are flagged for
   later promotion via `define-specialist --promote` (with reverse-PR
   suggestion to AMS specialist registry).

---

## Step 5 — Assembly manifest construction

For each accepted agent, build the Three Dimensions mapping:
- `name`
- `specialist` — path to specialist file (relative to target's `.claude/`)
- `standards` — list of paths (e.g. `standards/craft.md`,
  `standards/usability.md`)
- `peer` — peer agent name (logical pairing per specialist's recommendation)
- `environment_dependencies` — from specialist + cross-referenced with
  `environment_snapshot`
- `generated` — bool

Write into `config.json.assembly`.

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

## Step 10 — Seed everything into target's `.claude/`

Create `<target>/.claude/` and populate:

```
.claude/
├── settings.json            # from templates/hooks/settings.json.template
├── hooks/
│   └── scripts/
│       ├── setup-probe.sh
│       ├── session-init.sh
│       ├── prompt-anchor.sh
│       ├── commit-clean-pre-bash.sh
│       └── prescriptive-rules-block.sh
├── posture.md               # verbatim from templates/universal/
├── standards/
│   ├── craft.md
│   ├── safety.md
│   ├── usability.md
│   └── prose.md
├── specialists/             # only mapped specialists + _base-template
├── skills/
│   ├── update/SKILL.md           # frontmatter + procedures/update.md inlined
│   ├── deliver-work/SKILL.md     # frontmatter + procedures/deliver-work.md inlined
│   ├── audit-work/SKILL.md       # frontmatter + procedures/audit-work.md inlined
│   ├── finding/SKILL.md          # frontmatter + procedures/finding.md inlined
│   ├── define-specialist/SKILL.md
│   ├── commit-clean/SKILL.md
│   ├── jira-context/SKILL.md
│   └── tool-safety/SKILL.md      # generated per-project
├── audit/
│   ├── service.md           # verbatim from templates/audit/
│   ├── schema.md
│   └── indexes/
│       ├── README.md
│       └── schemas.md
├── patterns.md              # generated this run
├── approaches.md            # generated this run
├── config.json              # generated this run (assembly + env_snapshot + build_deploy + backlog)
├── prescriptive-rules.json  # generated this run
└── build-deploy.md          # generated this run
```

For each `templates/skills/<name>/SKILL.md`:
1. Read the template (frontmatter + `{{INLINE: procedures/<name>.md}}`).
2. Resolve `{{INLINE: ...}}` by reading the referenced procedure file from AMS.
3. The procedure may itself contain `@procedures/shared/<file>.md` references —
   resolve those by reading `procedures/shared/<file>.md` from AMS and inlining.
4. Recursively resolve until no AMS-relative path references remain. (Each
   shared procedure is inlined wherever it's referenced; the result is
   self-contained.)
5. Write the fully-resolved SKILL.md to the target.

After this step, the target has zero references back to AMS paths. Independence
test: rename AMS away — target still works.

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
