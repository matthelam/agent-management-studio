# Seeding

What `learn-codebase` copies into a target repo's `.claude/` directory, why,
and how it stays out of cloud git.

---

## Target `.claude/` layout

After `learn-codebase` completes, the target repo has:

```
<target>/
├── .git/
│   └── info/
│       └── exclude            ← Modified to exclude .claude/ (LOCAL ONLY)
├── .gitignore                 ← UNTOUCHED
└── .claude/
    ├── settings.json          ← Hook registrations
    ├── hooks/
    │   └── scripts/
    │       ├── setup-probe.sh
    │       ├── session-init.sh
    │       ├── prompt-anchor.sh
    │       ├── commit-clean-pre-bash.sh
    │       └── prescriptive-rules-block.sh
    ├── posture.md
    ├── standards/
    │   ├── craft.md
    │   ├── safety.md
    │   ├── usability.md
    │   └── prose.md
    ├── specialists/
    │   ├── _base-template.md
    │   ├── <agent-name>.md    ← One file per agent in this project's assembly
    │   └── ...
    ├── skills/
    │   ├── update/SKILL.md
    │   ├── deliver-work/SKILL.md
    │   ├── audit-work/SKILL.md
    │   ├── finding/SKILL.md
    │   ├── define-specialist/SKILL.md
    │   ├── commit-clean/SKILL.md
    │   ├── jira-context/SKILL.md
    │   └── tool-safety/SKILL.md
    ├── audit/
    │   ├── service.md
    │   ├── schema.md
    │   └── indexes/
    │       ├── README.md
    │       └── schemas.md
    ├── patterns.md            ← Generated this run
    ├── approaches.md          ← Generated this run
    ├── config.json            ← Generated this run (assembly + env_snapshot + build_deploy + backlog)
    ├── prescriptive-rules.json ← Generated from approaches.md GUARD RAILS
    └── build-deploy.md        ← Canonical build/test/deploy commands
```

---

## What's verbatim vs generated

| Type | Source | Verbatim or generated |
|---|---|---|
| Hook scripts | `templates/hooks/scripts/*.sh` | **Verbatim** copies |
| `settings.json` | `templates/hooks/settings.json.template` | **Verbatim** (template uses `$CLAUDE_PROJECT_DIR` resolved at runtime) |
| Posture | `templates/universal/posture.md` | **Verbatim** copy |
| Standards | `templates/universal/standards/*.md` | **Verbatim** copies |
| Specialist files | `templates/specialists/<name>.md` | **Verbatim** copies (only those in the project's assembly) |
| Audit harness | `templates/audit/{service,schema}.md` + `indexes/*` | **Verbatim** copies |
| Seeded skills | `templates/skills/<name>/SKILL.md` (frontmatter) + `procedures/<name>.md` (body) | **Generated** — frontmatter preserved; `{{INLINE: procedures/<name>.md}}` resolved by reading and substituting; recursively resolves `procedures/shared/<file>.md` references inside |
| Tool-safety skill | `templates/tool-safety/SKILL.md.template` + per-project registry slice | **Generated** with placeholder substitution |
| `patterns.md` | (no source — pure analysis output) | **Generated** |
| `approaches.md` | (no source — pure analysis output) | **Generated** |
| `config.json` | (no source) | **Generated** (assembly manifest + env snapshot + build/deploy + backlog) |
| `prescriptive-rules.json` | parsed from approaches.md GUARD RAILS | **Generated** |
| `build-deploy.md` | (no source) | **Generated** (Step 3 of learn-codebase) |

---

## Procedure inlining (how seeded skills become self-contained)

The flow at seed time:

```
templates/skills/update/SKILL.md (template):
  ---
  name: update
  description: Refresh the project's prescriptive layer ...
  ---

  # update

  {{INLINE: procedures/update.md}}
```

`learn-codebase` Step 10 reads the template and resolves placeholders:

1. Read `procedures/update.md`. Its body may contain `@procedures/shared/diff-engine.md`
   references.
2. For each `@procedures/shared/<file>.md` referenced inside, recursively
   resolve by reading the file and inlining its content in place.
3. Continue until no AMS-relative path references remain.
4. Write the resolved SKILL.md to `<target>/.claude/skills/update/SKILL.md`.

Result: the seeded SKILL.md is a self-contained markdown file. No external
dependencies. AMS could be deleted; the seeded skill still works.

---

## The `.git/info/exclude` strategy

**Critical:** AMS never modifies the tracked `.gitignore`. Modifying it would
itself reveal AI involvement (any reviewer reading `.gitignore` sees a
deliberate exclusion of tool-related paths). Instead:

- AMS appends to `<target>/.git/info/exclude`
- `.git/info/exclude` lives inside `.git/` — it is **never committed**
- It uses the same syntax as `.gitignore`
- Each clone of the repo has its own `.git/info/exclude` (per-machine)

The default exclusion is the entire `.claude/` directory:

```
# AMS-managed (do not commit)
.claude/
```

If the project already has its own use of `.claude/` that they intentionally
commit (e.g. project-level slash commands), `learn-codebase` warns and offers
fine-grained exclusion of only the AMS-specific subdirs.

### What if a different dev clones the repo?

They run `learn-codebase` on their machine. Their `.git/info/exclude` gets
the same entries. Their target gets seeded the same way. The seeding is
machine-local; the cloud repo never sees any of it.

If the dev wants a teammate's seeded artifacts to match exactly, they re-run
`learn-codebase` from the same AMS commit. AMS-version pinning is a v2
consideration if drift becomes a real problem.

---

## What CAN be committed

The architecture says zero AI footprint in cloud. But some things are
genuinely useful to commit if the dev wants:

- A `CLAUDE.md` at repo root with team-curated guidance for human
  contributors. AMS does not generate this; it's manual.
- The repo's existing `.gitignore`, `.editorconfig`, etc.
- Code, tests, docs.

AMS-seeded content goes in `.claude/` and is excluded. Anything outside
`.claude/` is the dev's call.

---

## Re-seeding

Running `learn-codebase` again on a repo with existing `.claude/`:

1. AMS detects existing `config.json` with `environment_snapshot` (Step 0).
2. Routes to update-or-rebuild prompt.
3. **Update** path: invokes `update` skill in the target. Existing assembly
   preserved; only detected diffs applied via human review gate.
4. **Rebuild** path: warns about overwriting; on confirm, regenerates all
   prescriptive artifacts.

For most ongoing maintenance, `update` (run from target) is the right tool —
it preserves manual edits and only changes what needs changing. `learn-codebase`
re-runs are for major restructures or when the AMS templates themselves have
materially evolved.

---

## Failure modes

| Failure | Effect |
|---|---|
| `.git/info/exclude` write fails (permissions) | Surface to dev; ask them to add `.claude/` manually |
| Target repo has uncommitted changes in `.claude/` | Surface; ask before overwriting |
| Inlining recursion can't resolve a reference | Error with the unresolved path; learn-codebase stops |
| Generated specialist rejected by dev mid-flow | Drop from team; continue with the rest |
| Hook script not executable on the dev's machine | learn-codebase runs `chmod +x .claude/hooks/scripts/*.sh`; if it fails (Windows), surface manual remediation |
