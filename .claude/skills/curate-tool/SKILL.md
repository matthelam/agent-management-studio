---
name: curate-tool
description: AMS maintenance skill for adding or refreshing entries in the tool catalogue. Accepts any tool candidate — MCP server (npm package, GitHub repo, hosted URL), skill pack (GitHub repo), or agent config — runs harness checks against tool-harness.md, performs mandatory gap analysis (§Gap), and writes approved entries to tool-catalogue.json, tech-tool-map.json, skill-pack-registry.json (skill packs), and tool-crud-profile.json (MCPs). Used by AMS curators, not seeded into target repos.
---

# curate-tool

AMS-only maintenance skill. Keeps `registries/tool-catalogue.json`,
`registries/tech-tool-map.json`, `registries/skill-pack-registry.json`, and
`registries/tool-crud-profile.json` current and quality-assured.

The harness this skill enforces is in `registries/tool-harness.md`.

---

## Invocation

```
curate-tool <candidate> [--type mcp|skill-pack|agent-config]
```

`<candidate>` can be:
- An npm package name: `next-devtools-mcp`
- A GitHub repo URL: `https://github.com/microsoft/skills`
- A hosted MCP URL: `https://mcp.labs.storyblok.com/mcp`
- A Claude Code plugin name: `shadcn`

`--type` is optional. If omitted, auto-detect from candidate shape.

---

## Run logging (mandatory)

**Every curate-tool invocation produces a structured run log** at
`<ams-root>/logs/curate-tool-<iso-timestamp>-<run-id>.jsonl`.

### At invocation start

1. Generate `RUN_ID` (UUIDv4).
2. Resolve `AMS_HOME`.
3. Compute `LOG_FILE=$AMS_HOME/logs/curate-tool-$(date -u +%Y-%m-%dT%H-%M-%S)-$RUN_ID.jsonl`.
4. Emit `invocation_start` with `{ "candidate": "<candidate>", "type": "<type>", "ams_version": "v2.2", "run_log": "<LOG_FILE>" }`.

### At each Step boundary

Emit `step_start` / `step_end` with `step_id` and `step_name`.

### Per-event emissions

| When | Event |
|---|---|
| Each automated harness check | `harness_check` with `dimension`, `outcome`, `score`, `notes` |
| Tool/skill list fetched | `tool_list_fetched` with `count` |
| Each manual harness check | `manual_harness_check` with `dimension`, `outcome`, `curator_notes` |
| Gap identified | `gap_identified` with `gap_description`, `gap_for` |
| Gap candidate found | `gap_candidate_found` with `candidate`, `action` (curate_now / queue) |
| Verdict computed | `harness_verdict` with full score table |
| Entry written | `artifact_write` + `tool_catalogued` with `tool_id`, `type`, `vendor`, `verdict` |
| Rejection | `tool_rejected` with `tool_id`, `reason` |
| Human gate | `human_gate` |
| Anomaly | `warn` or `error` |

### At invocation end

Emit `invocation_end` with `outcome`, `duration_ms`, `summary: { tool_id, type, verdict, registries_updated: [...], gaps_found: <n>, gaps_resolved: <n> }`.

### Log retention

Prune `$AMS_HOME/logs/curate-tool-*.jsonl` older than 7 days OR beyond the most-recent 50.

---

## Step 1 — Detect type and auto-check provenance

**Type detection (if --type omitted):**
- npm package or GitHub repo with `server` / `mcp` in name → `mcp`
- GitHub repo with SKILL.md files in a skills/ directory → `skill-pack`
- GitHub repo with agent personas / AGENTS.md / cognitive config → `agent-config`
- Ambiguous → ask curator

**Automated provenance checks:**

| Check | Source | Pass criteria |
|---|---|---|
| Vendor authenticity | github org / npm owner / domain | Org matches known vendor OR maintainer identity verifiable |
| Last commit recency | `gh repo view --json pushedAt` / npm metadata | < 90 days = active; 90-365 = stale-warning; > 365 = stale-fail (unless hosted with SLA) |
| Release cadence | git tags / npm versions | ≥ 1 release in past 180 days |
| License | LICENSE / package.json `license` | MIT, Apache-2.0, BSD-*, ISC, MPL-2.0 = pass; GPL-* = fail; unlicensed = fail; hosted = ToS review |
| Distribution | npm / plugin marketplace / hosted URL / Docker | Any one = pass |
| Documentation | README with non-trivial content | Pass = non-trivial; Fail = empty / missing |

Surface results:

```
AUTOMATED HARNESS — <candidate> (type: <type>)
  ✓ Vendor:          github.com/vercel/next-devtools-mcp — official Vercel org
  ✓ Last commit:     3 days ago
  ✓ Release cadence: 5 releases in last 90 days
  ✓ License:         MIT
  ✓ Distribution:    npm published as next-devtools-mcp
  ✓ Documentation:   README + tool list present
```

Hard fail on any of: GPL licence, unlicensed, unverifiable vendor, no install path.

---

## Step 2 — Enumerate tools / skills

**For MCPs:** Fetch the full method list (connect to server or read declared schema):
- Method name, parameters, return shape, documentation
- Present as markdown table

**For skill packs:** List all SKILL.md files found in the repo:
- Skill name, path, `description` from frontmatter, technologies covered
- Note total count; flag any without frontmatter

**For agent configs:** List personas, team compositions, guard rails, lenses found.

---

## Step 3 — Manual harness walkthrough (all types)

Walk through each dimension from `tool-harness.md`:

**Harness strength (§2)** — Score 1-5. Does this actively constrain AI or just inform it?
- For MCPs: does live data replace guessing? Does it block incorrect operations?
- For skill packs: does it encode anti-examples? Correct-vs-wrong pattern pairs?
- Score < 2 = hard fail (reject).

**Domain depth (§3)** — Score 1-5. How project-specific is the knowledge?

**Accuracy risk (§4)** — Are there known stale docs, wrong CRUD classifications, or deprecated patterns?

**Friction cost (§5)** — Score 1-5. Setup and maintenance burden.

**Composability (§6)** — Does it duplicate or conflict with existing curated tools?

**Security (§7)** — Credential handling, network calls, insecure recommendations.

**CRUD truthfulness (§8, MCPs only)** — Classify every method:
- `pure-read` / `read-with-side-effects` / `write` / `destructive`
- List side effects for `read-with-side-effects`

**Auth model (§10)** — Credential mechanism and safety.

---

## Step 4 — Gap analysis (mandatory)

After scoring harness strength, identify any coverage gap — where the tool
informs AI but doesn't fully constrain it.

**For each gap:**
1. Describe the gap concisely (e.g. "installs components but doesn't teach CVA/Radix usage patterns")
2. Search for a complementary tool that would close it:
   - Check `tool-catalogue.json` for existing approved tools covering the gap
   - Search npm / GitHub for candidates if none exists
3. If a candidate is found:
   - If viable (passes automated checks): initiate curation immediately (`curate-tool <candidate>`)
   - If deferred: add to catalogue with `gap_for: "<tool-id>"` and queue for next curation run
4. If no tool exists: note the gap in `harness.gaps` so learn-codebase generates a compensating domain skill

Emit `gap_identified` per gap found, `gap_candidate_found` per candidate evaluated.

---

## Step 5 — Score and verdict

Compile all dimension scores into a verdict per `tool-harness.md §Verdicts`:

| Condition | Verdict |
|---|---|
| All hards pass + soft scores ≥ 3 | `approved` |
| All hards pass + soft scores mixed | `approved (conditional)` — caveat required |
| Any hard fails | `rejected` |

Surface the full score table to the curator for confirmation before writing.

---

## Step 6 — Write registry entries (on approval)

### `tool-catalogue.json` (all types)

```json
{
  "id": "<tool-id>",
  "type": "mcp | skill-pack | agent-config",
  "name": "<human-friendly name>",
  "vendor": "<vendor>",
  "version": "<version>",
  "homepage": "<url>",
  "install": { "method": "<method>", "command": "<command>" },
  "auth_model": "<model>",
  "technologies": ["<tech-1>", "<tech-2>"],
  "tools": [...],
  "harness": {
    "scored_at": "<ISO-8601>",
    "verdict": "approved | approved (conditional) | rejected",
    "scores": { ... },
    "gaps": ["<gap-description>"],
    "notes": "<curator notes>"
  }
}
```

### `tech-tool-map.json`

Add the tool id under `mcps`, `skill_packs`, or `agent_configs` for each technology it serves.

### `skill-pack-registry.json` (skill packs only)

Add a source entry with `repo`, `structure`, `ingestion_model`, and per-skill entries under `skills`.

### `tool-crud-profile.json` (MCPs only)

For each method classified:

```json
{
  "tool_id": "<tool-id>",
  "method": "<method-name>",
  "version_range": "<latest-validated>",
  "crud_class": "pure-read | read-with-side-effects | write | destructive",
  "side_effects": ["<side-effect>"],
  "validated_at": "<ISO-8601>"
}
```

---

## Step 7 — Suggest reverse-PR (when relevant)

If the candidate was surfaced from a target project's `learn-codebase` run,
suggest opening a PR against `agent-management-studio` to add the entry to the
central registry for cross-project reuse.

The curator can:
- Commit the registry update as a regular AMS PR
- Defer (keep entry pending in a draft branch)

---

## Step 8 — Audit logging

Per `audit/schema.md`:
- `curate_tool_initiated` — candidate, type, source
- `harness_evaluated` — verdict, scores, gap count
- `tool_added` / `tool_rejected` — id, type, vendor, verdict, notes
- `gap_identified` / `gap_resolved` — per gap
- `crud_profile_added` — tool_id, method count (MCPs only)

---

## Failure handling

| Failure | Action |
|---|---|
| Network unavailable | Pause; curator can defer or proceed with manual checks |
| Candidate is private / auth-required | Surface; curator provides credentials or rejects |
| Tool list not enumerable automatically | Curator manually documents |
| Vendor authenticity ambiguous | Surface; curator decides |
| Hard fail on a gap candidate | Note gap as unresolvable; learn-codebase generates compensating skill instead |
