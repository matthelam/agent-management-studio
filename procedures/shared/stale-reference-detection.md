# Stale Reference Detection

After an `/update` is applied, scan all agent profiles for references to things that no longer exist in the environment and flag them as cleanup items.

---

## Purpose

An `/update` applies changes to directly affected profile sections, but stale references may exist elsewhere. If React was upgraded from 18 to 19 and the frontend-dev specialist knowledge was updated, the code-review agent might still reference `forwardRef` patterns in its review checklist. Stale reference detection catches these indirect references.

---

## Trigger

Stale reference detection runs automatically after `/update` Step 5 (Apply Approved Changes) completes and before Step 9 (Report Completion). It is a post-update validation sweep.

---

## Process

### Step 1 — Build Stale Reference List

From the applied changes, compile a list of things that are now outdated:

| Change Type | What becomes stale |
|-------------|-------------------|
| Major version bump | APIs deprecated in the new version, patterns superseded by new approaches |
| Tool replacement | All references to the old tool name, config, and patterns |
| Tool removal | All references to the removed tool |
| Structure change | References to old directory paths, old layout conventions |

### Step 2 — Scan Agent Profiles

For each item in the stale reference list, scan across:

| Profile Section | What to check |
|----------------|---------------|
| **Specialist knowledge** | Version-conditional rules, scope descriptions, boundary statements |
| **Standards** | References to tools or patterns in quality gate descriptions |
| **Project context** | `patterns.md` and `approaches.md` references to removed or changed tools |
| **Cross-agent references** | Peer pairing descriptions that reference changed capabilities |

The scan checks for textual references to the stale items — tool names, API names, pattern names, directory paths.

### Step 3 — Classify Findings

Each stale reference is classified:

| Severity | Criteria | Example |
|----------|----------|---------|
| **Warning** | Reference to a deprecated API or old pattern that still functions but is no longer recommended | code-review still mentions "check for proper useMemo usage" after React Compiler handles this |
| **Error** | Reference to something that no longer exists and would produce incorrect guidance | Specialist knowledge references Jest mock patterns after migration to Vitest |
| **Info** | Reference that is technically stale but low-risk | approaches.md mentions a config file that was renamed |

### Step 4 — Present as Cleanup Recommendations

Stale references are presented after the update completion report, as recommendations not auto-applied changes:

```
POST-UPDATE CLEANUP RECOMMENDATIONS

⚠ WARNING (1 item):
  code-review specialist: References "useMemo optimization checks" — React Compiler
  handles memoization automatically in React 19. Consider removing this guidance.

🔴 ERROR (1 item):
  backend-dev specialist: References "Jest mock patterns" — project migrated to Vitest.
  Mock syntax is incompatible. Update recommended.

ℹ INFO (1 item):
  approaches.md: References ".eslintrc.js" — project now uses "eslint.config.js" (flat config).

  [Address now] [Defer cleanup]
```

### Step 5 — Handle Human Response

| Action | Effect |
|--------|--------|
| **Address now** | Walk through each item with the same Review/Approve/Modify/Skip flow as the main update gate |
| **Defer cleanup** | Log the items for re-surfacing on next `/update`. Stored alongside `deferred_changes` |

---

## Scope Boundary

Stale reference detection scans for **textual references** within agent profile files. It does not:

- Scan application source code for stale patterns
- Validate that agent behaviour has actually changed
- Rewrite agent profiles automatically

It identifies where stale guidance may exist. The human decides what to do about it.
