# Change-to-Agent Resolution Logic

Takes a list of detected environment changes from the diff engine and determines which agents are affected and what parts of their profiles need updating.

---

## Purpose

The diff engine produces changes. The dependency mapping tells us which agents care. This resolution logic connects the two: for each change, it identifies affected agents and generates a proposed update description specifying what part of the agent's profile should change.

---

## Input

| Parameter | Source | Description |
|-----------|--------|-------------|
| `diff_report.changes` | Diff engine output | List of detected environment changes |
| `assembly.agents` | `config.json` | Agent profiles with `environment_dependencies` |

---

## Process

### Step 1 — Match Changes to Agents

For each change in `diff_report.changes`:

1. Read the change's `key` (e.g., `react`, `node`, `eslint`)
2. Scan all agents' `environment_dependencies` arrays for that key
3. Collect the list of affected agents

If no agents have the changed element in their dependencies, the change is classified as **informational** — reported but no agent updates proposed.

### Step 2 — Determine Update Scope

For each affected agent, determine which part of the profile needs updating:

| Change Type | Affected Profile Section | Rationale |
|-------------|------------------------|-----------|
| Version bump (same tool) | **Specialist knowledge** | Version-conditional rules may activate or deactivate |
| Tool replacement | **Specialist knowledge** + **Standards references** | New tool may require different expertise and quality gates |
| Tool addition | **Specialist knowledge** + **Environment dependencies** | Agent may need new version-conditional rules |
| Tool removal | **Specialist knowledge** + **Environment dependencies** | Remove references to the removed tool |
| Structure change | **Specialist knowledge** | Scope and file organisation rules may change |
| Content change (patterns/approaches) | **Project context** | All agents load patterns and approaches |

### Step 3 — Generate Proposed Updates

For each affected agent and change, generate a proposed update description:

```json
{
  "proposed_updates": [
    {
      "change_ref": "<reference to the diff change>",
      "agent": "frontend-dev",
      "impact": "major",
      "affected_sections": ["specialist_knowledge"],
      "description": "React 18 → 19: Remove manual useMemo/useCallback guidance (React Compiler handles this). Add 'use client' directive rules for Server Components. Add use() hook guidance. Update version-conditional rules.",
      "action_required": "review"
    },
    {
      "change_ref": "<reference to the diff change>",
      "agent": "code-review",
      "impact": "major",
      "affected_sections": ["specialist_knowledge"],
      "description": "React 18 → 19: Flag forwardRef usage as deprecated. Flag manual memoization as unnecessary unless profiling justifies it.",
      "action_required": "review"
    }
  ],
  "informational": [
    {
      "change_ref": "<reference to the diff change>",
      "key": "docker",
      "detail": "Docker version changed but no agents depend on it.",
      "action_required": "none"
    }
  ]
}
```

### Step 4 — Classify Action Required

Each proposed update gets an action classification:

| Action | When | Downstream |
|--------|------|------------|
| `review` | Major or medium impact changes | Presented in human review gate |
| `auto` | Minor impact, no specialist knowledge change | Can be auto-applied with `--auto` flag |
| `none` | Informational only, no agents affected | Reported but no action taken |

---

## Resolution Rules

### Content hash changes affect all agents

If `patterns_md` or `approaches_md` hashes changed, **every** agent on the project is affected because all agents load project context. These are always classified as `review`.

### Tool replacement triggers full specialist review

When a tool is replaced (e.g., Jest → Vitest), the affected agent's specialist knowledge needs a full review — not just a version number change but a rewrite of tool-specific guidance.

### Unaffected agents are never touched

If an agent does not have the changed element in its `environment_dependencies`, it receives no proposed update, even if the change is major. The dependency mapping is the single source of truth for "who cares about this change."

### Multiple changes may affect the same agent

An agent can appear in multiple proposed updates if multiple environment elements it depends on changed simultaneously. These are presented as separate review items — the human reviews each independently.

---

## Consumers

| Consumer | How it uses the resolution output |
|----------|----------------------------------|
| Human review gate (`/update`) | Presents each proposed update for approve/modify/skip/defer |
| Migration intelligence | Enriches `review` items with migration-specific guidance |
| Cascade detection | Groups related proposed updates into logical cascades |
