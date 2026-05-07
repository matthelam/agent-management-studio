# Backlog Integration — Schema Reference

Defines the data structures used by the backlog integration layer.

---

## State-Level: `state.json` Jira Block

Written by `/connect --jira`. Read by all `/work` commands to determine if backlog mode is active.

```json
{
  "jira": {
    "cloud_id": "uuid",
    "project_key": "SCRUM",
    "site_name": "my-site.atlassian.net",
    "configured_at": "ISO-8601"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `cloud_id` | string (UUID) | Atlassian Cloud ID for API calls |
| `project_key` | string | Jira project key (e.g. `SCRUM`, `PROJ`) |
| `site_name` | string | Human-readable site name for display |
| `configured_at` | string (ISO-8601) | When the connection was established |

**Presence rule:** If the `jira` block exists in `state.json`, backlog mode is ON. If absent, backlog mode is OFF. No other flag or setting controls this.

**Lifecycle:** Written once during `/connect --jira`. Cleared when a new `/connect` runs without `--jira`. Never modified in-place.

---

## Project-Level: `config.json` Backlog Section

Written by `/init` when it detects a `jira` block in `state.json`. Persisted in the project profile for use by the delivery engine.

```json
{
  "backlog": {
    "provider": "jira",
    "cloud_id": "uuid",
    "project_key": "PROJ",
    "configured_at": "ISO-8601"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `provider` | string | Always `"jira"` — reserved for future provider extensibility |
| `cloud_id` | string (UUID) | Atlassian Cloud ID |
| `project_key` | string | Jira project key for this project's backlog |
| `configured_at` | string (ISO-8601) | When the config was written |

**Resolution order:** When determining the active backlog config, the delivery engine checks:

1. Project `config.json` `.backlog` section (project-specific)
2. Studio `state.json` `.jira` block (session-level)
3. Absent — backlog mode is unavailable

The first non-null result wins.

---

## Priority-to-Urgency Mapping

Used when populating work items from Jira tickets.

| Jira Priority | Work Item Urgency |
|---------------|-------------------|
| Blocker | critical |
| High | elevated |
| Medium | normal |
| Low | normal |
| Lowest | normal |

---

## Issue Type-to-Mode Hint

Used as a suggestion when populating work items from Jira tickets. The human confirms or overrides.

| Jira Issue Type | Mode Hint |
|-----------------|-----------|
| Bug | fix |
| Story | change |
| Task | change |
| Epic | change |
| Sub-task | inherited from parent |
