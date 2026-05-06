# update Procedure

Refresh the project's prescriptive layer. Consolidates the OLD `/rescan` (read-only
environment diff) + OLD `/update` (apply flow) + the new behavioural-drift
distillation from claude-mem observations.

**Modes:**

- `update` — full apply flow (env drift + behavioural drift, unified review gate)
- `update --preview` — read-only diff (replaces standalone `/rescan`)
- `update --auto` — auto-apply minor changes; gate major and medium
- `update --env-only` — env drift only (skip behavioural distillation)
- `update --behavioural-only` — behavioural drift only (skip env scan)

---

## Step 1 — Preconditions

1. Verify claude-mem worker reachable —
   `curl -sf http://127.0.0.1:37777/api/health`. If unreachable AND mode requires
   behavioural data: surface remediation (`npx claude-mem start`); offer to fall
   back to `--env-only`.
2. Verify required tech-stack CLIs/MCPs are present per `config.json` (this
   absorbs the OLD `bootstrap-deps` skill's role).
3. Read seeded `config.json.environment_snapshot` — record baseline timestamp.

---

## Step 2 — Environment-drift diff

Inlined from OLD rescan logic + diff-engine:

@procedures/shared/diff-engine.md

@procedures/shared/cascade-detection.md

@procedures/shared/stale-reference-detection.md

1. Perform fresh scan (same logic as `learn-codebase` Step 1) producing fresh
   `environment_snapshot` in memory.
2. Run diff engine against stored snapshot.
3. Apply cascade-detection: a single change can affect multiple agents — surface
   the cascade.
4. Apply stale-reference-detection: identify references to dependencies that
   have been removed or moved.
5. Produce structured `diff_report`.

If `--preview` mode: format the diff report for human consumption (grouped by
impact: major / medium / minor / unchanged) and stop. Recommend running `update`
without `--preview` to apply.

---

## Step 3 — Behavioural-drift distillation

(Skip this step if `--env-only`.)

1. Query claude-mem observations scoped by project:
   `curl 'http://127.0.0.1:37777/api/search?project=<name>&dateStart=<since-last-update>&limit=200'`
2. Batch-fetch full observations via `get_observations(ids=...)`.
3. Distil observation evidence into proposed pattern/approach updates:
   - **Recurring patterns** in observations not yet in `patterns.md` →
     proposed addition
   - **Patterns in `patterns.md`** with no recent supporting observations →
     proposed deprecation flag
   - **Contradictions** between recent observations and existing patterns →
     proposed amendment with both versions surfaced
   - **New approaches** repeatedly observed → proposed addition to
     `approaches.md`
4. Each proposed update carries supporting observation IDs (provenance).
5. Apply confidence scoring: 1 session ≠ pattern; ≥5 sessions in last 30 days =
   pattern candidate.
6. Produce structured `behavioural_diff` with proposals categorised by
   confidence (high/medium/low).

---

## Step 4 — Resolve affected agents

@procedures/shared/change-to-agent-resolution.md

For each env change AND each behavioural proposal:

1. Look up affected agents via `environment_dependencies` (env changes) or by
   pattern-domain mapping (behavioural changes).
2. Determine which profile sections need updating (specialist knowledge,
   standards refs, env_dependencies, patterns.md, approaches.md).
3. Generate proposed update descriptions.

---

## Step 5 — Check deferred changes

Load `deferred_changes` from `config.json`. Re-surface alongside new diff +
behavioural results:

```
⚠ N DEFERRED CHANGE(S) (from <date>):
  - <change>
  Reason: <defer reason>
```

Deferred items are included in the unified review flow.

---

## Step 6 — Unified human review gate

@procedures/shared/human-review-gate.md

1. Present unified summary: env changes + behavioural proposals + deferred items.
2. Walk through each proposed change: Review / Approve / Modify / Skip / Defer.
3. Offer batch approval for minor changes (in `--auto` mode, minor changes with
   `action_required: auto` are auto-approved).
4. Major and medium changes always go through the full review gate.
5. Behavioural proposals show supporting observation IDs so dev can drill into
   evidence.
6. Collect all decisions before applying any changes.

---

## Step 7 — Apply approved changes

For each approved change:

1. **Update specialist knowledge** — modify the agent's specialist file (in
   target's `.claude/specialists/`) per the proposed update.
2. **Update standards references** — add or remove standards if the change
   warrants it.
3. **Update environment_dependencies** — add or remove entries.
4. **Update patterns.md** — add new patterns, deprecate stale ones, amend
   contradicted ones (each with provenance comment linking to source observation
   IDs).
5. **Update approaches.md** — same.
6. **Regenerate prescriptive-rules.json** — re-parse approaches.md GUARD RAILS
   to refresh the deterministic blocklist.

Order: specialist knowledge → standards → dependencies → patterns/approaches →
prescriptive-rules regeneration.

---

## Step 8 — Persist deferred + update snapshot

1. Write newly deferred changes to `config.json.deferred_changes` array.
2. Remove deferred changes that were approved or skipped this session.
3. Replace `config.json.environment_snapshot` with the fresh snapshot.
4. Append summary entry to `config.json.update_history`:

```json
{
  "timestamp": "ISO-8601",
  "changes_detected": <count>,
  "changes_applied": <count>,
  "changes_deferred": <count>,
  "changes_skipped": <count>,
  "behavioural_proposals_applied": <count>,
  "agents_updated": ["..."]
}
```

5. Re-seed the target's `.claude/` artifacts that depend on registry slices
   (tool-safety regen if relevant CRUD profiles changed).

---

## Step 9 — Report completion

```
UPDATE COMPLETE
  Env changes detected:    <n>
  Env changes applied:     <n> (<auto-approved-count> auto)
  Env changes deferred:    <n>
  Env changes skipped:     <n>
  Behavioural proposals:   <n>
  Behavioural applied:     <n>
  Agents updated:          <list>
  Snapshot updated:        ISO-8601

  Deferred items will be re-surfaced on next /update.
```

---

## Step 10 — Audit logging

Each step emits events via `audit/service.md`:

- `update_initiated` (Step 1) — flags, deferred re-surfaced count
- `behavioural_query` (Step 3) — observation count, proposal count
- `update_decision` (Step 6) — per change: action, modifications, defer reason
- `update_applied` (Step 7) — per agent per change: sections modified
- `update_completed` (Step 9) — summary

Schema reference: `audit/schema.md`.
