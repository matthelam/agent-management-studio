# Environment Diff Engine

Compare two environment snapshots and produce a categorized list of changes with impact levels.

---

## Purpose

The diff engine is the core comparison mechanism. It takes a **stored snapshot** (from `config.json`) and a **fresh snapshot** (from a new scan) and produces a structured diff report.

The diff engine is read-only. It compares and reports. It never modifies files.

---

## Input

| Parameter | Source | Description |
|-----------|--------|-------------|
| `stored_snapshot` | `config.json` → `environment_snapshot` | The baseline snapshot from the last `/init` or `/update` |
| `fresh_snapshot` | New scan of the project | A freshly generated snapshot using the same schema |

---

## Process

### Step 1 — Schema Version Check

Compare `schema_version` between stored and fresh snapshots.

- **Same version:** Proceed with field-by-field comparison.
- **Fresh is newer:** Proceed, but note new fields as informational additions.
- **Stored is newer:** This should not happen. Flag as an error — the schema definition may be out of sync.

### Step 2 — Field-by-Field Comparison

Walk each section of the snapshot and compare values:

| Section | Comparison method |
|---------|------------------|
| `runtime` | Compare each key's version string using semver parsing |
| `package_manager` | Compare `name` (equality) and `version` (semver) |
| `frameworks` | Compare each key's version string using semver parsing |
| `testing` | Compare `runner` and `e2e` objects — both `name` (equality) and `version` (semver) |
| `linting` | Compare each key's version string using semver parsing |
| `key_dependencies` | Compare each key's version string using semver parsing |
| `structure` | Compare each field by string equality |
| `content_hashes` | Compare hash strings by equality |

**For each field, detect:**

- **Unchanged** — values are identical
- **Version changed** — same tool, different version
- **Tool replaced** — different tool name in the same slot
- **Tool added** — key exists in fresh but not stored
- **Tool removed** — key exists in stored but not fresh
- **Structure changed** — layout, test location, or config files differ
- **Content changed** — hash differs (for `patterns_md` or `approaches_md`)

### Step 3 — Classify Impact Level

Each detected change is classified by impact:

| Impact | Criteria | Examples |
|--------|----------|---------|
| **Major** | Major version bump (semver X.0.0), tool replacement, structure change | React 18 → 19, Jest → Vitest, pages/ → app/ |
| **Medium** | Tool addition or removal, content hash change, minor version bump with known breaking behaviour | Added Playwright, removed Enzyme, patterns.md changed |
| **Minor** | Patch or minor version bump with no known breaking behaviour | React 18.2.0 → 18.3.0, ESLint 8.56.0 → 8.57.0 |

**Version bump classification rules:**

- Parse versions using semver (major.minor.patch)
- Major digit change → **Major**
- Minor digit change → **Medium** if the tool is a framework; **Minor** if it is a utility/linter
- Patch digit change → **Minor**
- If version cannot be parsed as semver, fall back to string comparison and classify as **Medium**

### Step 4 — Build Diff Report

Produce a structured diff object. This is data, not a formatted string — downstream consumers (the `/rescan` report formatter, the `/update` flow) format it as needed.

**Diff report structure:**

```json
{
  "diff_report": {
    "timestamp": "<ISO 8601 timestamp of diff execution>",
    "stored_snapshot_timestamp": "<timestamp from stored snapshot>",
    "schema_versions": {
      "stored": 1,
      "fresh": 1
    },
    "summary": {
      "total_changes": 0,
      "major": 0,
      "medium": 0,
      "minor": 0,
      "unchanged": 0
    },
    "changes": [
      {
        "section": "<snapshot section name>",
        "key": "<field key>",
        "change_type": "<version_changed|tool_replaced|tool_added|tool_removed|structure_changed|content_changed>",
        "impact": "<major|medium|minor>",
        "stored_value": "<previous value or null>",
        "fresh_value": "<new value or null>",
        "detail": "<human-readable description of the change>"
      }
    ],
    "unchanged": [
      {
        "section": "<snapshot section name>",
        "key": "<field key>",
        "value": "<current value>"
      }
    ]
  }
}
```

---

## Edge Cases

| Scenario | Handling |
|----------|---------|
| No stored snapshot exists | Return a special diff with `stored_snapshot_timestamp: null` and all fresh fields listed as `tool_added` with impact **Medium**. This indicates a first-time scan or legacy config. |
| New field in fresh snapshot | Treat as `tool_added` with impact **Medium**. The stored snapshot predates this field. |
| Field in stored but not fresh | Treat as `tool_removed` with impact **Medium**. The tool may have been uninstalled. |
| Null values | `null` in stored + value in fresh = `tool_added`. Value in stored + `null` in fresh = `tool_removed`. Both `null` = unchanged. |
| Non-semver versions | Fall back to string equality. If different, classify as **Medium** with `change_type: version_changed`. |
| Content hash changed but file deleted | Treat as `content_changed` with impact **Major**. Flag for human review. |

---

## Consumers

| Consumer | How it uses the diff |
|----------|---------------------|
| `/rescan` | Formats the diff report as a human-readable summary |
| `/update` | Uses the changes list to drive agent-to-environment resolution and the human review gate |
| Stale snapshot warning | Uses `stored_snapshot_timestamp` to determine profile age |
