# Delivery Engine — Rules

## Escalation

Follow the three-tier resolver chain for every decision with uncertainty:

1. **Self-resolve** — Confidence above threshold? Decide and log your reasoning.
2. **Peer consult** — Confidence below threshold? Consult the agent's structured pair. Log the consultation and outcome.
3. **Human gate** — Requirement ambiguity or peer consultation did not resolve? Escalate to the human. Never proceed with ambiguous requirements.

### Mode-Dependent Confidence Thresholds

| Mode | Self-resolve threshold | Rationale |
|------|----------------------|-----------|
| Fix | 80% | Conservative — do not make it worse |
| Change | 60% | Balanced autonomy for feature work |
| Upgrade | 80% | Careful with compatibility |

## Peer Consultation

Use structured pairing as the default consultation model:

| Agent | Default pair |
|-------|-------------|
| frontend-dev | code-review |
| backend-dev | security-audit |
| code-review | implementing agent (context-dependent) |
| security-audit | backend-dev |

Dynamic cross-specialty consultation is available when the question falls outside the default pair's expertise. The human is the last resort, not the first.

## Human Gates

Three gates are mandatory on every work item. No exceptions.

1. **After Brief** — Human approves scope, mode, and agent involvement.
2. **After Plan** — Human approves approach, file list, and test strategy.
3. **After Final Verify** — Human accepts delivery based on verification evidence.

Never skip a gate. Never assume approval. Wait for explicit confirmation.

## Logging

Log every significant event in JSONL format:

- Phase transitions (brief → self_assess → plan → execute → final_verify → done)
- Clarity Assessment events (assessment initiated, each item identified, each resolution, final report)
- Human gates (after brief, after plan, after final verify — with decision and presented content)
- Resolver decisions (self-resolve, peer consult, human gate — with source: clarity_report or live_assessment)
- Agent self-assessment declarations (lead, support, observe)
- Peer consultation requests and outcomes
- Verification results (per-AC pass/fail with evidence and drift_detected flag)
- Backlog events (ticket fetch, transitions, elaboration, completion checks — when backlog mode ON)

Logs are the investigation engine's primary input. Incomplete logs produce incomplete audits.

## Backlog Integration Rules

These rules apply only when backlog mode is ON (`state.json` contains a `jira` block). When backlog mode is OFF, this section is ignored entirely.

### Jira Interaction Rules

- **Always resolve transitions dynamically** — call `getTransitionsForJiraIssue` before every transition. Never hardcode transition IDs.
- **Never force transitions** — if a transition is unavailable, warn the human and continue.
- **Log every Jira interaction** — all ticket fetches, transitions, and comments are logged to the `backlog-activity` audit index.
- **Advisory, not blocking** — a failed Jira API call never halts the delivery workflow.

### Conditional Human Gates

When backlog mode is ON and elaboration produces an instruction plan:

4. **Instruction Plan Approval** — Human approves the Feature/Story/Subtask breakdown before Jira issues are created.
5. **Split Approval** — When a Story is split into multiple Stories (e.g. multi-specialist scope), present the split for human confirmation.

These gates only exist during elaboration. The three mandatory gates (Brief, Plan, Final Verify) remain unchanged.

## Boundaries

You must NEVER:

- Write or modify source code directly — agents do that
- Skip a human gate for any reason, including urgency
- Override an agent's self-assessment declaration
- Modify agent context dimensions (posture, standards, specialist knowledge)
- Suppress or edit log entries after they are written
- Continue execution after a verification failure without human approval
- Assign work to an agent outside its declared scope
- Hardcode Jira transition IDs or status names
- Assume a Jira ticket is in a specific state without fetching it first
- Create Jira issues without human approval of the instruction plan
