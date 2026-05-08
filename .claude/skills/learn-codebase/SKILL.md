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

## Canonical step order

Steps MUST execute in this exact sequence. Each step asserts its required
input artifacts exist before doing any work. Skipping or reordering a step
will cause the next step's assertion to fail hard.

```
Step 0   → .run-<RUN_ID>/run-state.json          preflight + IDs
Step 0.5 → .run-<RUN_ID>/gitignore.done          protection before any file write
Step 1   → .run-<RUN_ID>/sweep-manifest.json     file list
Step 2   → .run-<RUN_ID>/environment-snapshot.json   [HUMAN GATE — stack approval]
Step 3   → .run-<RUN_ID>/build-deploy.json       canonical commands
Step 6   → <target>/.claude/patterns.md          LLM analysis (reads sweep-manifest)
Step 7   → <target>/.claude/approaches.md        LLM analysis (reads sweep-manifest)
Step 8   → <target>/.claude/prescriptive-rules.json  parsed from approaches.md
Step 4   → .run-<RUN_ID>/cognitive-team.json     [HUMAN GATE — team + prefix approval]
Step 4b  → .run-<RUN_ID>/domain-skills-manifest.json  LLM generates per-tech skills
Step 5   → <target>/.claude/config.json          assembly manifest
Step 9   → <target>/.claude/skills/tool-safety/SKILL.md  template substitution
Step 10  → .run-<RUN_ID>/seed.done               copy all artifacts to target
Step 12  → .run-<RUN_ID>/observations.done       claude-mem seeding
Step 13  → audit log entry
Step 14  → final report + cleanup
```

**Why Steps 6/7 precede Step 4:** domain skill generation (Step 4b) must read
`patterns.md` and `approaches.md` as input. Running analysis before the team
gate also means the dev sees detected patterns when approving the team shape.
The prior ordering (4 before 6/7) was a latent bug — 4b referenced files that
didn't yet exist.

---

## Artifact directory

All intermediate artifacts live in:

```
$AMS_HOME/logs/.run-<RUN_ID>/
```

This directory is created by Step 0 and cleaned up only at `invocation_end`.
It persists across Bash tool calls (each call is a fresh shell — variables
don't, but files do).

### Standard bash preamble (every bash block)

Copy this verbatim at the top of **every** Bash tool call in this skill. It
reloads state from disk and defines the assertion helpers:

```bash
AMS_HOME="C:/Repositories/agent-management-studio"
RUN_ID="$(cat "$AMS_HOME/logs/.current-run-id" 2>/dev/null || echo "")"
LOG_FILE="$(cat "$AMS_HOME/logs/.current-run-log" 2>/dev/null || echo "")"
ARTIFACT_DIR="$AMS_HOME/logs/.run-$RUN_ID"

emit_event() {
  [ -z "$LOG_FILE" ] && return
  local event_type="$1" level="${2:-info}" step="${3:-null}" payload="$4"
  printf '{"timestamp":"%s","run_id":"%s","skill":"learn-codebase","event_type":"%s","level":"%s","step":%s,"payload":%s}\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)" "$RUN_ID" "$event_type" "$level" \
    "$([ "$step" = "null" ] && echo "null" || printf '"%s"' "$step")" \
    "${payload:-{\}}" >> "$LOG_FILE"
}

assert_artifact() {
  local path="$1" label="${2:-$1}"
  if [ ! -s "$path" ]; then
    echo "GATE FAIL: required artifact missing or empty: $label"
    echo "The preceding step did not complete. Halting."
    exit 1
  fi
}

assert_approved() {
  local path="$1" label="${2:-$1}"
  if ! grep -q '"approved":.*true' "$path" 2>/dev/null; then
    echo "GATE FAIL: human approval required."
    echo "Edit $label and set \"approved\": true, then re-run from this step."
    exit 1
  fi
}
```

`AMS_HOME` must be the absolute path to the AMS checkout. Adjust if the cwd
differs from the canonical location.

---

## Run logging (mandatory, threads through every step)

Every invocation produces a structured run log at:
`$AMS_HOME/logs/learn-codebase-<ISO_TIMESTAMP>-<RUN_ID>.jsonl`

Schema and event taxonomy: `procedures/ams-audit-logging.md`.

### Invocation-start block (run once, before Step 0)

```bash
AMS_HOME="C:/Repositories/agent-management-studio"
RUN_ID="$(python3 -c 'import uuid; print(uuid.uuid4())')"
mkdir -p "$AMS_HOME/logs"
TIMESTAMP="$(date -u +%Y-%m-%dT%H-%M-%S)"
LOG_FILE="$AMS_HOME/logs/learn-codebase-${TIMESTAMP}-${RUN_ID}.jsonl"
ARTIFACT_DIR="$AMS_HOME/logs/.run-$RUN_ID"
mkdir -p "$ARTIFACT_DIR"

echo "$LOG_FILE" > "$AMS_HOME/logs/.current-run-log"
echo "$RUN_ID"   > "$AMS_HOME/logs/.current-run-id"

# emit_event is defined in the standard preamble above; define inline here too
emit_event() {
  local event_type="$1" level="${2:-info}" step="${3:-null}" payload="$4"
  printf '{"timestamp":"%s","run_id":"%s","skill":"learn-codebase","event_type":"%s","level":"%s","step":%s,"payload":%s}\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)" "$RUN_ID" "$event_type" "$level" \
    "$([ "$step" = "null" ] && echo "null" || printf '"%s"' "$step")" \
    "${payload:-{\}}" >> "$LOG_FILE"
}

emit_event "invocation_start" "info" "null" \
  "{\"args\":[\"$TARGET_PATH\"],\"cwd\":\"$(pwd)\",\"ams_version\":\"v2.2\",\"run_log\":\"$LOG_FILE\"}"
```

Prune logs older than 7 days OR beyond the most-recent 50 at invocation start.

### At each step boundary

Emit `step_start` before work; `step_end` after with `outcome` and `duration_ms`.

### Event taxonomy

| When | Emit |
|---|---|
| Probing a dependency | `dependency_probe` |
| Writing to target `.claude/` | `artifact_write` with path, bytes, sha256 |
| Skipping a planned write | `artifact_skip` with reason |
| Step 4 team proposal/approval | `cognitive_team_proposed`, `cognitive_team_approved` |
| Step 4b each domain skill | `domain_skill_generated` |
| Step 6 each pattern | `pattern_detected` |
| Step 7 each approach | `approach_detected` |
| Step 8 each rule | `prescriptive_rule_generated` |
| Any human review point | `human_gate` |
| Non-fatal anomaly | `warn` |
| Fatal failure | `error` |

### At invocation end

Emit `invocation_end`:
```json
{ "outcome": "success|failure|stopped",
  "duration_ms": <total>,
  "summary": {
    "steps_completed": <n>, "steps_skipped": <n>,
    "artifacts_written": <n>, "patterns_detected": <n>,
    "approaches_detected": <n>, "guard_rails_extracted": <n>,
    "prescriptive_rules_generated": <n>,
    "domain_skills_generated": <n>,
    "synthetic_observations_seeded": <n>
  }
}
```

Then clean up sidecar files and artifact directory:
```bash
rm -f "$AMS_HOME/logs/.current-run-log" "$AMS_HOME/logs/.current-run-id"
rm -rf "$ARTIFACT_DIR"
```

### Error path

On any unhandled error: emit `error`, then `invocation_end` with
`outcome: "failure"`, then clean up sidecars. Never let a failure propagate
silently.

---

## Step 0 — Preflight

**Assertions at step start:** none (this is the first step).

Emit `step_start` with `step_id: "0"`, `step_name: "preflight"`.

Hard probes — any failure emits `error` + `invocation_end` + halts:

1. **claude-mem worker reachable:** `curl -sf --max-time 5 http://127.0.0.1:37777/api/health`
   On failure: emit `dependency_probe` with `outcome: "unreachable"`,
   remediation hint `npx claude-mem start`. Stop — do not continue with a
   partial seed.
2. **Bun installed:** `bun --version`. On missing: emit `error` and stop.
3. **Target path is a git repo:** directory exists and contains `.git/`.
   On failure: emit `error` and stop.
4. **Resolve claude-mem project ID:**
   - `target_basename = basename(<target-path>)`
   - Synthetic observations in Step 12 always use `target_basename` — never
     the auto-detected AMS-side ID.
   - Emit `claude_mem_project_id_resolved` with `target_basename` and reason.
5. **Check for existing seed:** if `<target>/.claude/config.json` exists with
   `environment_snapshot`, offer update-vs-rebuild prompt. Emit `human_gate`
   with the decision.

**Artifact produced:** write `$ARTIFACT_DIR/run-state.json`:
```json
{
  "run_id": "<RUN_ID>",
  "ams_home": "<AMS_HOME>",
  "target_path": "<TARGET_PATH>",
  "target_basename": "<TARGET_BASENAME>",
  "log_file": "<LOG_FILE>",
  "started_at": "<ISO>",
  "flags": ["--strict"],
  "preflight_passed": true
}
```

Emit `step_end` for Step 0.

---

## Step 0.5 — Early gitignore protection

**Assertions at step start:**
```bash
assert_artifact "$ARTIFACT_DIR/run-state.json" "run-state.json (Step 0)"
```

Append `.claude/` to `<target>/.git/info/exclude` before any file is seeded.
Idempotent — check for existing entry first. **NEVER touch the tracked
`.gitignore`.**

If this step fails (permissions, not a git repo, etc.): emit `error` and stop.
The seed must not proceed without the protection layer.

**Artifact produced:** write `$ARTIFACT_DIR/gitignore.done`:
```json
{"step": "gitignore-protection", "target": "<target>", "entries_added": [".claude/"], "completed_at": "<ISO>"}
```

Emit `gitignore_update` with `entries_added` and `entries_already_present`.

---

## Step 1 — File sweep

**Assertions at step start:**
```bash
assert_artifact "$ARTIFACT_DIR/run-state.json"   "run-state.json (Step 0)"
assert_artifact "$ARTIFACT_DIR/gitignore.done"   "gitignore.done (Step 0.5)"
```

Read every source file in the target. Each Read fires claude-mem hooks;
observations are captured passively. **Do NOT separately invoke claude-mem's
`learn-codebase` skill** — that would be a redundant second sweep.

Files to read:
- All source files (by extension, language-aware)
- `package.json`, `*.csproj`, `*.sln`, `pom.xml`, `build.gradle`,
  `requirements.txt`, `pyproject.toml`, `Cargo.toml`, `go.mod`
- Config files: `tsconfig.json`, `.eslintrc*`, `.prettierrc*`,
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

**Artifact produced:** write `$ARTIFACT_DIR/sweep-manifest.json`:
```json
{
  "files_read": ["<path1>", "<path2>", "..."],
  "file_count": <n>,
  "completed_at": "<ISO>"
}
```

---

## Step 2 — Stack detection

**Assertions at step start:**
```bash
assert_artifact "$ARTIFACT_DIR/sweep-manifest.json" "sweep-manifest.json (Step 1)"
```

Produce structured `environment_snapshot` from the files in `sweep-manifest.json`:
- `runtime` — Node, Python, .NET version etc.
- `package_manager` — npm/pnpm/yarn/poetry/nuget version
- `frameworks` — primary frameworks with exact versions
- `testing` — test runners, e2e tools, visual regression
- `linting` — ESLint, Prettier etc.
- `key_dependencies` — significant libraries (state, styling, validation)
- `structure` — monorepo vs single-app, src layout, package directories

**Human gate:** present scan results to dev. Confirm detected stack is correct.
Allow corrections. Do NOT write the artifact until the dev has confirmed.

**Artifact produced:** write `$ARTIFACT_DIR/environment-snapshot.json` with
all fields above, and initially `"approved": false`. After dev confirmation,
set `"approved": true` in the file. Downstream steps will fail their
`assert_approved` check until this is done.

```json
{
  "schema_version": 1,
  "runtime": { ... },
  "package_manager": { ... },
  "frameworks": { ... },
  "testing": { ... },
  "linting": { ... },
  "key_dependencies": { ... },
  "structure": { ... },
  "approved": true
}
```

Emit `human_gate` with the dev's response.

---

## Step 3 — Build/deploy intelligence

**Assertions at step start:**
```bash
assert_artifact "$ARTIFACT_DIR/environment-snapshot.json" "environment-snapshot.json (Step 2)"
assert_approved "$ARTIFACT_DIR/environment-snapshot.json" "environment-snapshot.json"
```

### Documentation-first

Read `README.md`, `CONTRIBUTING.md`, `BUILD.md`, `DEPLOY.md`, etc. (already
in sweep-manifest; analyse now). Extract documented build/test/deploy commands
verbatim with their source file and line number.

### Code-second

Inspect:
- `package.json` `scripts` section
- Makefile / Taskfile.yml / justfile — top-level targets
- `*.csproj` / `*.sln` — MSBuild targets
- `Dockerfile` / `docker-compose.yml` — container build steps
- `turbo.json` / `nx.json` — pipeline definitions
- `sitecore.json` / Sitecore CLI configs — serialization commands
- CI/CD pipeline files — what does CI actually run?

### Solution-type classification

Match against `registries/build-deploy-signatures.json`:
- **headless** — Next.js / Nuxt / SvelteKit; Vercel / Netlify / Cloudflare
- **dotnet** — .csproj/.sln; dotnet/MSBuild
- **sitecore-xmc** — `sitecore.json` + `*.scproj` + SCS signals
- **sitecore-jss** — Sitecore JSS (headless + content)
- **hybrid-sitecore-content-sdk** — Next.js + Sitecore Content SDK
- **other** — fallback; surface signature for human classification

### Synthesis — one canonical command per concern

Reconcile docs vs code. Surface conflicts to dev. Produce:
- `canonical_build`, `canonical_test`, `canonical_deploy`
- `canonical_content_sync` (Sitecore-style only)
- `prerequisites` — env vars, services, credentials needed

Do NOT auto-execute commands. Surface for manual verification.

**Artifact produced:** write `$ARTIFACT_DIR/build-deploy.json`:
```json
{
  "solution_type": "...",
  "canonical_build": "...",
  "canonical_test": "...",
  "canonical_deploy": "...",
  "canonical_content_sync_push": "...",
  "canonical_content_sync_pull": "...",
  "prerequisites": [ "..." ],
  "conflicts_surfaced": [ "..." ],
  "completed_at": "<ISO>"
}
```

Also write `<target>/.claude/build-deploy.md` (human-readable version).
Emit `artifact_write` for `build-deploy.md`.

---

## Step 6 — Pattern detection

**Assertions at step start:**
```bash
assert_artifact "$ARTIFACT_DIR/sweep-manifest.json" "sweep-manifest.json (Step 1)"
assert_artifact "$ARTIFACT_DIR/build-deploy.json"   "build-deploy.json (Step 3)"
```

Scan codebase for recurring coding patterns. Default mode produces descriptive
patterns; `--strict` produces hard rules.

@procedures/shared/diff-engine.md *(used for pattern recognition signals)*

Categories to scan: state management, data fetching, error handling, file
organization, naming conventions, test patterns, component patterns, API
patterns, CMS wrapper patterns (Sitecore-aware), deployment patterns.

**Strict mode output format** (each pattern):
```
RULE: <constraint>
DO <permitted action> ONLY when <condition>
DO NOT <prohibited action>
RATIONALE: <evidence: file paths with line numbers, counts>
EXAMPLE (correct): <code snippet>
EXAMPLE (wrong): <code snippet>
```

**Artifact produced:** write `<target>/.claude/patterns.md`.
Emit `pattern_detected` per pattern found.
Emit `artifact_write` for `patterns.md` with byte count and sha256.

---

## Step 7 — Approach detection

**Assertions at step start:**
```bash
assert_artifact "$ARTIFACT_DIR/sweep-manifest.json"  "sweep-manifest.json (Step 1)"
# patterns.md must exist — Step 6 must have completed
TARGET_PATH="$(python3 -c "import json; print(json.load(open('$ARTIFACT_DIR/run-state.json'))['target_path'])")"
assert_artifact "$TARGET_PATH/.claude/patterns.md"   "patterns.md (Step 6)"
```

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

GUARD RAILS must be machine-parseable into `prescriptive-rules.json` in Step 8.
Each guard rail line must follow the exact format:
```
  - <path or glob> — <READ ONLY|BLOCK|MODIFY WITH CAUTION> [for agents|description]
```

**Artifact produced:** write `<target>/.claude/approaches.md`.
Emit `approach_detected` per approach found.
Emit `artifact_write` for `approaches.md` with byte count and sha256.

---

## Step 8 — Generate `prescriptive-rules.json`

**Assertions at step start:**
```bash
TARGET_PATH="$(python3 -c "import json; print(json.load(open('$ARTIFACT_DIR/run-state.json'))['target_path'])")"
assert_artifact "$TARGET_PATH/.claude/approaches.md" "approaches.md (Step 7)"
```

Parse GUARD RAILS sections from `approaches.md`. For each guard rail line:

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
- File path patterns (glob → `path_glob`)
- Bash command patterns (regex → `command_regex`)
- Multi-file rules (cross-package boundaries)

On parse failure for any single guard rail: emit `warn` with the unparsed
line; continue parsing remaining entries. Surface all unparsed entries to dev
at end of step.

**Artifact produced:** write `<target>/.claude/prescriptive-rules.json`.
Emit `prescriptive_rule_generated` per rule.
Emit `artifact_write` for `prescriptive-rules.json`.

---

## Step 4 — Cognitive team proposal

**Assertions at step start:**
```bash
assert_artifact "$ARTIFACT_DIR/environment-snapshot.json" "environment-snapshot.json (Step 2)"
assert_approved "$ARTIFACT_DIR/environment-snapshot.json" "environment-snapshot.json"
TARGET_PATH="$(python3 -c "import json; print(json.load(open('$ARTIFACT_DIR/run-state.json'))['target_path'])")"
assert_artifact "$TARGET_PATH/.claude/patterns.md"        "patterns.md (Step 6)"
assert_artifact "$TARGET_PATH/.claude/approaches.md"      "approaches.md (Step 7)"
assert_artifact "$TARGET_PATH/.claude/prescriptive-rules.json" "prescriptive-rules.json (Step 8)"
```

Cognitive harnesses are HOW agents think; domain skills (Step 4b) are WHAT
they know. This step decides the team shape; Step 4b generates per-tech
domain knowledge.

### Default-team proposal heuristics

| Project signal | Suggested default team | Reason |
|---|---|---|
| UI-heavy (React + Tailwind/Radix + Storybook) | `[empiricist, specifist, synthesizer]` + accessibility lens | Specifist for UI detail; synthesizer to integrate UI patterns |
| Sitecore + accelerator + monorepo | `[architect, empiricist, specifist, synthesizer]` | Architect for cross-package boundaries |
| .NET backend | `[skeptic, empiricist, architect]` + security lens | Backend services need adversarial review |
| Greenfield prototype | `[pragmatist, synthesizer]` | Move fast |
| Compliance-heavy | `[systematist, skeptic, empiricist]` + security + devils-advocate | Process completeness |

### Primary harness for single-mode

| Project shape | primary_harness_for_single_mode |
|---|---|
| (default) | `empiricist` |
| Compliance-heavy | `systematist` |
| Prototype-heavy | `pragmatist` |
| Architectural-decision-heavy | `architect` *(expensive — Opus)* |

### Audit primary harness

| Project shape | audit_primary_harness |
|---|---|
| (default) | `empiricist` |
| Security-sensitive | `skeptic` |
| Architecture-debt-heavy | `architect` |

### Default lenses

| Project signal | default_lenses |
|---|---|
| UI-heavy / consumer-facing | `[accessibility]` |
| Security-sensitive (auth, payments, PII) | `[security]` |
| Performance-critical | `[performance]` |

### Work item prefix derivation

Derive `WORK_ITEM_PREFIX` from target repo name: take first letter of each
hyphen-separated word, uppercase, max 3 chars.
Examples: `aceik-sandpit-xmc` → `ASX`; `my-app` → `MA`.

### Human review gate

Surface the proposed team AND derived prefix to the dev:

```
COGNITIVE TEAM PROPOSAL — <project-name>

Default team:
  - empiricist  (Sonnet)
  - specifist   (Sonnet)
  - synthesizer (Opus)

Single-agent default: empiricist (Sonnet)
Audit-work default:   skeptic (Sonnet)
Default lenses:       accessibility
Work item prefix:     ASX

Approve, modify, or override?
```

Dev can accept / modify (swap harnesses, lenses, prefix).

**Artifact produced:** write `$ARTIFACT_DIR/cognitive-team.json` with
`"approved": false` initially. After dev confirmation, set `"approved": true`.

```json
{
  "cognitive_team": ["empiricist", "specifist", "synthesizer"],
  "primary_harness_for_single_mode": "empiricist",
  "audit_primary_harness": "skeptic",
  "default_lenses": ["accessibility"],
  "altitude_band_default": "maker",
  "synthesis_harness": "synthesizer",
  "work_item_prefix": "ASX",
  "approved": true
}
```

Emit `human_gate` and `cognitive_team_approved` after confirmation.

---

## Step 4b — Dynamic domain-skill generation

**Assertions at step start:**
```bash
assert_artifact "$ARTIFACT_DIR/cognitive-team.json"       "cognitive-team.json (Step 4)"
assert_approved "$ARTIFACT_DIR/cognitive-team.json"       "cognitive-team.json"
TARGET_PATH="$(python3 -c "import json; print(json.load(open('$ARTIFACT_DIR/run-state.json'))['target_path'])")"
assert_artifact "$TARGET_PATH/.claude/patterns.md"        "patterns.md (Step 6)"
assert_artifact "$TARGET_PATH/.claude/approaches.md"      "approaches.md (Step 7)"
```

For each detected major technology, generate a project-specific domain skill.

### Granularity constraint: umbrella, not fine-grained

**One domain skill per major tech category.** Internal sections cover
sub-concerns. Target: 6–10 domain skills per project.

Canonical tech categories and their umbrella skill names:

| Tech signals detected | Umbrella skill name |
|---|---|
| `@sitecore-content-sdk/*`, `@sitecore-feaas/*`, `sitecore.json`, `*.scproj` | `sitecore-knowledge` |
| `next`, `@next/*` | `nextjs-knowledge` |
| `tailwindcss`, `@radix-ui/*`, `class-variance-authority` | `tailwind-radix-knowledge` |
| `@mantine/*` | `mantine-knowledge` |
| `turbo`, `turbo.json`, `nx.json` | `monorepo-turbo-knowledge` |
| `@storybook/*` | `storybook-knowledge` |
| `docker`, `Dockerfile` | `docker-knowledge` |

Do NOT create separate skills for sub-concerns of an umbrella (e.g. do NOT
create `sitecore-serialization-knowledge`, `sitecore-xmc-knowledge`, AND
`sitecore-content-sdk-knowledge` separately — these all belong inside
`sitecore-knowledge`). If a tech doesn't match a canonical category, use
`<tech>-knowledge` and note it in `domain-skills-manifest.json`.

### Per-tech generation

For each umbrella skill:

1. **Pull the registry slice** from `registries/tech-mcp-map.json`,
   `registries/mcp-catalogue.json`, `registries/tool-crud-profile.json`.

2. **Extract project-specific context** from:
   - GUARD RAILS in `approaches.md` mentioning this tech
   - Patterns in `patterns.md` mentioning this tech
   - CLI commands from `build-deploy.json` relevant to this tech
   - File paths in `sweep-manifest.json` where this tech appears

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
<canonical commands from build-deploy.json slice>

## MCP methods (when applicable)
<curated list from mcp-catalogue with concrete invocation examples>

## Doc fallback
If uncertain, search <official_docs_url> before improvising.
This project uses version <version>.
```

4. Write to `<target>/.claude/skills/<skill-name>/SKILL.md`.
   Emit `domain_skill_generated` and `artifact_write` per skill.

### Storybook special case (mandatory when detected)

If Storybook is in `sweep-manifest.json`, `storybook-knowledge` MUST include
`*.stories.tsx`, `*.stories.ts`, `*.stories.jsx` as explicit file-pattern
proximity triggers and the phrase **"MANDATORY PRE-CONDITION: invoke this
skill before writing any .stories.tsx file"** in the description.

The skill body MUST include a Testing API section: `@storybook/test` play
functions, `userEvent`, `expect`, component interaction assertions, Playwright
run commands, and a complete story example with `play` function.

**Artifact produced:** write `$ARTIFACT_DIR/domain-skills-manifest.json`:
```json
{
  "skills_generated": ["sitecore-knowledge", "nextjs-knowledge", "..."],
  "skill_count": <n>,
  "completed_at": "<ISO>"
}
```

---

## Step 5 — Assembly manifest construction

**Assertions at step start:**
```bash
assert_artifact "$ARTIFACT_DIR/environment-snapshot.json"  "environment-snapshot.json (Step 2)"
assert_artifact "$ARTIFACT_DIR/build-deploy.json"          "build-deploy.json (Step 3)"
assert_artifact "$ARTIFACT_DIR/cognitive-team.json"        "cognitive-team.json (Step 4)"
assert_approved "$ARTIFACT_DIR/cognitive-team.json"        "cognitive-team.json"
assert_artifact "$ARTIFACT_DIR/domain-skills-manifest.json" "domain-skills-manifest.json (Step 4b)"
```

Build `config.json` by combining all approved intermediate artifacts:

```json
{
  "project": "<target-basename>",
  "assembly": {
    "cognitive_team": ["empiricist", "specifist", "synthesizer"],
    "domain_knowledge": ["sitecore-knowledge", "nextjs-knowledge", "..."],
    "default_lenses": ["accessibility"],
    "primary_harness_for_single_mode": "empiricist",
    "audit_primary_harness": "skeptic",
    "altitude_band_default": "maker",
    "synthesis_harness": "synthesizer"
  },
  "environment_snapshot": { "<contents of environment-snapshot.json minus 'approved' field>" },
  "audit": {
    "work_item_prefix": "<from cognitive-team.json>",
    "next_counter": 1,
    "db_path": ".claude/audit"
  },
  "deferred_changes": [],
  "update_history": []
}
```

`domain_knowledge` array is taken directly from `domain-skills-manifest.json`
`skills_generated`. `environment_snapshot` embeds `build-deploy.json` fields
under `build_deploy`. The `approved` field from intermediate artifacts is
**not** carried into `config.json` — it is only a run-time gate.

After writing, compute SHA-256 of `patterns.md` and `approaches.md` and store
in `environment_snapshot.content_hashes`.

**Artifact produced:** write `<target>/.claude/config.json`.
Emit `artifact_write` for `config.json`.

---

## Step 9 — Generate per-project `tool-safety` skill

**Assertions at step start:**
```bash
TARGET_PATH="$(python3 -c "import json; print(json.load(open('$ARTIFACT_DIR/run-state.json'))['target_path'])")"
assert_artifact "$TARGET_PATH/.claude/config.json"                "config.json (Step 5)"
assert_artifact "$TARGET_PATH/.claude/prescriptive-rules.json"    "prescriptive-rules.json (Step 8)"
```

Read `templates/tool-safety/SKILL.md.template`. Substitute:
- `{{PROJECT_NAME}}` — target's name
- `{{TIMESTAMP}}` — ISO-8601 now
- `{{TOOL_PROFILE_VERSION}}` — version of `tool-crud-profile.json`
- `{{TECH_MAP_VERSION}}` — version of `tech-mcp-map.json`
- `{{TOOL_CRUD_TABLE}}` — markdown table of CRUD profiles for stack tools
- `{{VERSION_CHECKS}}` — version-check commands for stack tools
- `{{SCOPED_ACCESS_TABLE}}` — mirror of GUARD RAILS in lookup form

**Artifact produced:** write `<target>/.claude/skills/tool-safety/SKILL.md`.
Emit `artifact_write`.

---

## Step 10 — Seed everything into target's `.claude/`

**Assertions at step start:**
```bash
TARGET_PATH="$(python3 -c "import json; print(json.load(open('$ARTIFACT_DIR/run-state.json'))['target_path'])")"
assert_artifact "$TARGET_PATH/.claude/config.json"                     "config.json (Step 5)"
assert_artifact "$TARGET_PATH/.claude/prescriptive-rules.json"         "prescriptive-rules.json (Step 8)"
assert_artifact "$TARGET_PATH/.claude/patterns.md"                     "patterns.md (Step 6)"
assert_artifact "$TARGET_PATH/.claude/approaches.md"                   "approaches.md (Step 7)"
assert_artifact "$TARGET_PATH/.claude/skills/tool-safety/SKILL.md"    "tool-safety/SKILL.md (Step 9)"
assert_artifact "$ARTIFACT_DIR/domain-skills-manifest.json"           "domain-skills-manifest.json (Step 4b)"
```

Copy the remaining static artifacts from AMS into `<target>/.claude/`:

```
.claude/
├── CLAUDE.md                    # templates/CLAUDE.md.template — {{WORK_ITEM_PREFIX}} substituted
├── settings.json                # templates/hooks/settings.json.template
├── hooks/scripts/
│   ├── setup-probe.sh
│   ├── session-init.sh
│   ├── prompt-anchor.sh
│   ├── audit-write.sh
│   ├── commit-clean-pre-bash.sh
│   └── prescriptive-rules-block.sh
├── harnesses/                   # only those in assembly.cognitive_team + primary + audit
├── lenses/                      # all four standard lenses
├── posture.md                   # templates/universal/posture.md
├── standards/craft.md           # templates/universal/standards/
├── standards/safety.md
├── standards/usability.md
├── standards/prose.md
├── skills/update/SKILL.md       # {{INLINE: procedures/update.md}} resolved
├── skills/deliver-work/SKILL.md
├── skills/audit-work/SKILL.md
├── skills/finding/SKILL.md
├── skills/define-specialist/SKILL.md
├── skills/commit-clean/SKILL.md
├── skills/jira-context/SKILL.md
├── skills/query-audit/SKILL.md  # {{WORK_ITEM_PREFIX}} substituted
├── audit/service.md
├── audit/schema.md
├── audit/indexes/README.md
└── audit/indexes/schemas.md
```

All dynamically-generated files (config.json, patterns.md, approaches.md,
prescriptive-rules.json, build-deploy.md, tool-safety/SKILL.md, domain
skills) are already in place from prior steps.

### CLAUDE.md seeding

Seed `templates/CLAUDE.md.template` → `<target>/.claude/CLAUDE.md`,
substituting `{{WORK_ITEM_PREFIX}}`. This file enforces the `deliver-work`
kickoff gate on every session. Overwrite if already present.

### Procedural skill seeding

For each procedural skill template:
1. Read the template.
2. Resolve `{{INLINE: procedures/<name>.md}}` by reading from AMS.
3. Recursively resolve `@procedures/shared/<file>.md` references.
4. Substitute `{{WORK_ITEM_PREFIX}}` where present.
5. Write to target.

### Hook script seeding

Copy each script from `templates/hooks/scripts/` and make executable:
```bash
chmod +x "<target>/.claude/hooks/scripts/"*.sh
```

`audit-write.sh` is mandatory. Verify both its `UserPromptSubmit` and
`PostToolUse(*)` registrations are present in the seeded `settings.json`.

### Audit directory

```bash
mkdir -p "<target>/.claude/audit/work-items"
mkdir -p "<target>/.claude/audit/indexes"
```

**Artifact produced:** write `$ARTIFACT_DIR/seed.done`:
```json
{"step": "seed", "artifacts_written": <n>, "completed_at": "<ISO>"}
```

Emit `artifact_write` for every file copied.

---

## Step 12 — Seed claude-mem with synthetic init observations

**Assertions at step start:**
```bash
assert_artifact "$ARTIFACT_DIR/seed.done" "seed.done (Step 10)"
```

For each detected pattern / approach / build-step / specialist-decision,
emit a synthetic observation:

```bash
curl -X POST http://127.0.0.1:37777/api/observations \
  -H 'Content-Type: application/json' \
  -d '{
    "type": "init-discovery",
    "project": "<target-basename>",
    "title": "<short title>",
    "narrative": "<evidence-based narrative>",
    "concepts": ["<concept1>", "..."],
    "files_read": ["<path1>", "..."]
  }'
```

Always use `target_basename` from `run-state.json` as the project tag — never
the AMS-side project ID.

On failure of any observation: emit `warn`, continue, log to
`<target>/.claude/audit/errors.jsonl`. Warn dev that update's baseline will
be missing for any failed observations.

**Artifact produced:** write `$ARTIFACT_DIR/observations.done`:
```json
{"step": "observations", "observations_seeded": <n>, "failures": <n>, "completed_at": "<ISO>"}
```

Emit `claude_mem_observation_seeded` per observation.

---

## Step 13 — Audit-log the init

**Assertions at step start:**
```bash
assert_artifact "$ARTIFACT_DIR/observations.done" "observations.done (Step 12)"
```

Emit `learn_codebase_completed` via the seeded audit service:

```json
{
  "type": "learn_codebase_completed",
  "actor": "system",
  "payload": {
    "target_path": "<absolute path>",
    "stack_summary": { "<from environment-snapshot.json>" },
    "domain_skills_generated": ["<from domain-skills-manifest.json>"],
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

```
LEARN-CODEBASE COMPLETE
  Target:         <absolute path>
  Profile:        <target>/.claude/
  Stack:          <summary>
  Domain skills:  <count>  (<list>)
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

Emit `invocation_end` with full summary. Clean up:
```bash
rm -f "$AMS_HOME/logs/.current-run-log" "$AMS_HOME/logs/.current-run-id"
rm -rf "$ARTIFACT_DIR"
```

---

## Failure handling

| Failure | Action |
|---|---|
| claude-mem worker unreachable | Stop at Step 0; emit remediation hint |
| Target path doesn't exist | Stop at Step 0 |
| Assertion gate fails | Stop at the failing step; message names the missing artifact and which step produces it |
| Existing config detected | Route to update-or-rebuild prompt (Step 0) |
| Stack detection ambiguous | Surface to dev; allow correction at Step 2 gate |
| GUARD RAILS parse failure | Skip rule; emit `warn`; surface unparsed entries to dev |
| Synthetic observation seed fails | Continue; log to `audit/errors.jsonl`; warn dev |
| `.git/info/exclude` write fails | Surface; ask dev to add manually; halt |

---

## Idempotence

On a target with existing `config.json`, Step 0 offers update-vs-rebuild.
On full rebuild, all artifacts are overwritten. Hand-edited sections in
`patterns.md`/`approaches.md` are preserved when the content hash in
`config.json.environment_snapshot.content_hashes` matches — if hashes differ,
warn before overwriting.
