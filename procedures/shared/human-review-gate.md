# Human Review Gate Flow

The review gate presents each proposed agent profile change to the human for approval before any modifications are applied.

---

## Principle

No agent profile is modified without explicit human approval. The review gate is the control point between "here's what changed" and "apply the change." All proposed updates are collected and presented before any are applied — there is no partial application mid-review.

---

## Input

| Parameter | Source | Description |
|-----------|--------|-------------|
| `proposed_updates` | Change-to-agent resolution output | List of proposed changes with affected agents and profile sections |
| `informational` | Change-to-agent resolution output | Changes with no agent impact |

---

## Process

### Step 1 — Present Summary

Show the human a summary of all detected changes and proposed updates before entering item-by-item review:

```
UPDATE REVIEW
Changes detected: 5 (2 major, 2 medium, 1 minor)
Agents affected: 3 (frontend-dev, backend-dev, code-review)
Proposed updates: 4
Informational: 1

Proceed to review? (yes / abort)
```

If the human aborts, no changes are applied and the flow ends.

### Step 2 — Item-by-Item Review

Present each proposed update individually. Major impact items are presented first, then medium, then minor.

**Review presentation format:**

```
[1/4] 🔴 MAJOR — frontend-dev
  Change: react 18.2.0 → 19.0.0
  Affects: Specialist knowledge (version-conditional rules)
  Proposed update:
    - Remove manual useMemo/useCallback guidance (React Compiler handles this)
    - Add 'use client' directive rules for Server Components
    - Add use() hook guidance
    - Update version-conditional rule thresholds

  Action: [Review] [Approve] [Modify] [Skip] [Defer]
```

### Step 3 — Handle Human Response

For each proposed update, the human selects one of five actions:

| Action | Effect | Persistence |
|--------|--------|------------|
| **Review** | Show the exact before/after diff of what changes in the agent's profile. Return to action selection after review. | None — just viewing |
| **Approve** | Mark this change for application. The proposed update will be applied as-is when the review completes. | Queued for application |
| **Modify** | The human edits the proposed update before approving. The modified version is queued for application. | Queued for application (modified) |
| **Skip** | Leave this agent unchanged for this change. No update is applied, and the change is not tracked for re-surfacing. | Permanent for this change |
| **Defer** | Acknowledge the change exists but do not apply it yet. The deferred change is persisted and re-surfaced on the next `/rescan` or `/update`. | Persisted in `config.json` |

### Step 4 — Deferred Changes Persistence

Deferred changes are stored in `config.json` under a `deferred_changes` array:

```json
{
  "deferred_changes": [
    {
      "deferred_at": "2026-02-19T14:30:00Z",
      "change_key": "react",
      "change_type": "version_changed",
      "stored_value": "18.2.0",
      "fresh_value": "19.0.0",
      "affected_agent": "frontend-dev",
      "reason": "Team hasn't adopted React 19 patterns yet"
    }
  ]
}
```

On subsequent `/rescan` or `/update` runs, deferred changes are re-surfaced with a note:

```
⚠ DEFERRED (2026-02-19): react 18.2.0 → 19.0.0 for frontend-dev
  Reason: Team hasn't adopted React 19 patterns yet
  Action: [Approve] [Modify] [Skip] [Defer again]
```

### Step 5 — Batch Approve for Minor Changes

When minor changes are reached in the review, offer batch approval:

```
MINOR CHANGES (1 item):
  eslint 8.56.0 → 8.57.0 → affects: code-review

  [Batch approve all minor] [Review individually]
```

This accelerates review when many low-impact changes exist without sacrificing control.

### Step 6 — Confirm Before Application

After all items are reviewed, present a final summary before applying:

```
REVIEW COMPLETE
  Approved: 3 changes
  Modified: 0 changes
  Skipped: 0 changes
  Deferred: 1 change

  Apply 3 approved changes? (yes / abort)
```

If the human confirms, proceed to application. If they abort, nothing is applied and all decisions are discarded (except deferred items already persisted).

---

## Consumers

| Consumer | How it uses the review gate |
|----------|---------------------------|
| `/update` command | Orchestrates the full flow: rescan → resolve → review gate → apply |
| Migration intelligence | Enriches the review presentation with migration-specific guidance |
| Cascade detection | Groups related items in the review presentation |
