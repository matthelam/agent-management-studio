---
name: curate-mcp
description: AMS maintenance skill for adding or refreshing entries in the MCP catalogue. Takes a candidate MCP (URL, npm package, or github repo), runs automated harness checks (provenance, maintenance health, distribution, license), walks the curator through manual harness items (functional fit, CRUD-truthfulness, vendor authenticity), scores against mcp-harness.md, and writes the approved entry to mcp-catalogue.json + tech-mcp-map.json + tool-crud-profile.json. Used by AMS curators, not seeded into target repos.
---

# curate-mcp

AMS-only maintenance skill. Used to keep `registries/mcp-catalogue.json`,
`registries/tech-mcp-map.json`, and `registries/tool-crud-profile.json` current
and quality-assured.

The harness this skill enforces is in `registries/mcp-harness.md`.

---

## Invocation

```
curate-mcp <candidate>
```

`<candidate>` can be:
- An npm package name: `@modelcontextprotocol/server-postgres`
- A github repo URL: `https://github.com/anthropic/mcp-server-x`
- A direct MCP server URL (for hosted MCPs)

---

## Run logging (mandatory)

**Every curate-mcp invocation produces a structured run log** at
`<ams-root>/logs/curate-mcp-<iso-timestamp>-<run-id>.jsonl`. Schema in
`procedures/ams-audit-logging.md`.

### At invocation start

1. Generate `RUN_ID` (UUIDv4).
2. Resolve `AMS_HOME`.
3. Compute `LOG_FILE=$AMS_HOME/logs/curate-mcp-$(date -u +%Y-%m-%dT%H-%M-%S)-$RUN_ID.jsonl`.
4. Define `emit_event` per `procedures/ams-audit-logging.md`.
5. Emit `invocation_start` with payload `{ "candidate": "<candidate>",
   "ams_version": "v2.1", "run_log": "<LOG_FILE>" }`.

### At each Step boundary

Emit `step_start` and `step_end` with `step_id` matching the step number
and `step_name` matching the heading.

### Per-event emissions inside steps

| When | Emit |
|---|---|
| Step 1 — each automated harness check (last commit, license, etc.) | `harness_check` with `dimension`, `outcome`, `score`, `notes` |
| Step 2 — fetched the candidate's tool list | `mcp_tool_list_fetched` with `tool_count` |
| Step 3 — each manual curator-walked check | `manual_harness_check` with `dimension`, `outcome`, `curator_notes` |
| Step 4 — verdict computed | `harness_verdict` with the full per-dimension score table |
| Step 5 — entry written to `mcp-catalogue.json` | `artifact_write` with the path, plus `mcp_catalogued` with `mcp_id`, `vendor`, `verdict`, `crud_methods_classified` |
| Step 5 — `tech-mcp-map.json` updated | `artifact_write` for the path |
| Step 5 — CRUD entries added to `tool-crud-profile.json` | `artifact_write` plus per-method count |
| On rejection (verdict = rejected) | `mcp_rejected` with `mcp_id`, `reason` |
| Step 6 — reverse-PR suggestion | `human_gate` with `decision` |
| Any human review point | `human_gate` |
| Any anomaly | `warn` or `error` |

### At invocation end

Emit `invocation_end` with `outcome`, `duration_ms`, `summary: { mcp_id,
verdict, methods_classified, registries_updated: [...] }`.

### Log retention

At invocation start, prune `$AMS_HOME/logs/curate-mcp-*.jsonl` older than
7 days OR beyond the most-recent 50 (whichever keeps more).

---

## Step 1 — Automated harness checks

Run all of these without human intervention:

| Check | Source | Pass criteria |
|---|---|---|
| **Last commit recency** | `gh repo view --json pushedAt` or npm metadata | < 90 days for "active"; 90-365 = "stale-warning"; > 365 = "stale-fail" |
| **Release cadence** | git tags / npm versions | At least one release in past 180 days for active projects |
| **License** | LICENSE file / package.json `license` | Allowed list: MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC, MPL-2.0. Forbidden: GPL-* (incompatible with AMS goals), unlicensed |
| **Issue responsiveness** | github issues (open count, time-to-first-response on recent) | Responsive maintainership signal; soft check |
| **Vendor authenticity (auto-check)** | If npm: package owner matches expected org; if github: org matches expected vendor | Hard fail if a brand name (e.g. "vercel-mcp") is published by an unrelated user |
| **Distribution discoverability** | Published to npm / available via plugin marketplace / has install instructions | Hard requirement |
| **Documentation present** | README.md exists with non-trivial content; tool list documented | Hard requirement |
| **Schema/tool list machine-readable** | Server exposes `tools/list` MCP method or has a manifest | Soft requirement; surface absence to curator |

Surface results as a structured report:

```
AUTOMATED HARNESS — <candidate>
  ✓ Last commit:    23 days ago
  ✓ Release cadence: 3 releases in last 90 days
  ✓ License:         MIT
  ⚠ Issue responsiveness: 12 open issues, latest response > 30 days
  ✓ Vendor authenticity:  github.com/anthropic/<repo> matches official Anthropic org
  ✓ Distribution:    npm published as @anthropic/...
  ✓ Documentation:   README + tool list present
  ✓ Schema:          tools/list method exposed
```

If any **hard requirement** fails, mark the candidate as **harness fail** and
report — the curator can still proceed manually if there's a special case.

---

## Step 2 — Fetch & surface tool/method list

Connect to the MCP candidate (or read its declared schema) and enumerate:

- Each tool/method name
- Each method's declared parameters
- Each method's declared return shape
- Documentation per method (where available)

Present to the curator as a markdown table for review.

---

## Step 3 — Manual harness items (curator walkthrough)

Walk the curator through each:

**Vendor authenticity (manual confirmation)** — does this MCP actually come
from the technology vendor it claims to manage? E.g., is "Vercel MCP" actually
from Vercel? Curator confirms or rejects.

**Documentation quality** — is the README clear about what the MCP does, how
to install it, what permissions it needs? Curator scores 1-5.

**Functional fit** — does this MCP actually cover the use cases the technology
needs? Specifically the operations developers do most often. Curator scores
1-5 with notes.

**CRUD-truthfulness review (per method)** — for each tool/method:
- Does the doc claim "read"/"get"/"list" — and does it ACTUALLY only read?
- Does the method write logs, telemetry, lock files, mtime, cache, or any
  other side effect even when documented as "read"?
- Curator classifies each method: `pure-read`, `read-with-side-effects`,
  `write`, or `destructive`.
- Notes the side effects for `read-with-side-effects` cases.

**Auth model** — OAuth / SSO / API key / passwordless? Are credentials
expected to be in env vars (good) or configured per-machine (acceptable) or
hardcoded (reject)?

**Security posture** — any obvious red flags? Unauthorized network calls?
Asks for credentials it shouldn't need?

**Stability** — versioning policy declared? Breaking change history? Curator
score 1-5.

---

## Step 4 — Score against `mcp-harness.md`

Combine automated + manual results into a structured score:

| Dimension | Pass / Fail / Conditional |
|---|---|
| Provenance | ... |
| Maintenance | ... |
| Distribution | ... |
| Documentation | ... |
| Stability | ... |
| Security | ... |
| CRUD truthfulness | ... |
| License | ... |
| Auth model | ... |
| Functional fit | ... |

**Verdict** — `approved`, `conditional` (approved with caveats — caveat must
be documented in the catalogue entry), or `rejected` (do not add).

---

## Step 5 — Write registry entries (on approval)

### `mcp-catalogue.json`

```json
{
  "id": "<candidate-id>",
  "name": "<human-friendly name>",
  "vendor": "<vendor-name>",
  "version": "<latest-version>",
  "homepage": "<url>",
  "install": {
    "method": "npm | plugin-marketplace | docker | other",
    "command": "<install command>"
  },
  "auth_model": "oauth | api_key | sso | passwordless | none",
  "harness": {
    "scored_at": "ISO-8601",
    "verdict": "approved | conditional | rejected",
    "scores": { "provenance": 5, "maintenance": 4, ... },
    "notes": "..."
  },
  "tools": [...]
}
```

### `tech-mcp-map.json`

Add the MCP id under each technology key it serves:

```json
{
  "next.js": {
    "mcps": ["next-devtools", "<new-id>"],
    "skills": [...],
    "specialists": ["frontend-dev"]
  }
}
```

### `tool-crud-profile.json`

For each method classified in Step 3, write an entry:

```json
{
  "tool_id": "<candidate-id>",
  "method": "<method-name>",
  "version_range": "<latest-validated>",
  "crud_class": "pure-read | read-with-side-effects | write | destructive",
  "side_effects": ["<side-effect-1>", "<side-effect-2>"],
  "validated_at": "ISO-8601"
}
```

---

## Step 6 — Suggest reverse-PR (when relevant)

If the candidate came in from a target project's `learn-codebase` proposal
(via `define-specialist --promote` or similar), suggest:

> *"This MCP was first encountered in project `<name>`. Consider opening a PR
> against `agent-management-studio` to add this entry to the central registry
> for re-use across other projects."*

The curator can choose to:
- Commit the registry update as a regular AMS PR
- Defer (keep the entry pending in a draft branch)

---

## Step 7 — Audit logging

Per `audit/schema.md`:
- `curate_mcp_initiated` — candidate, source
- `harness_evaluated` — verdict, scores
- `mcp_added` / `mcp_rejected` — id, vendor, verdict, notes
- `crud_profile_added` — tool_id, method count

---

## Failure handling

| Failure | Action |
|---|---|
| Network unavailable for harness checks | Pause; curator can defer or proceed with manual checks |
| Candidate is private/auth-required | Surface; curator provides credentials or rejects |
| Schema cannot be enumerated automatically | Curator manually documents tool list |
| Vendor authenticity ambiguous | Surface; curator decides |
