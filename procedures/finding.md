# /finding Procedure

Create a structured finding — an observation backed by evidence, with a severity classification and an actionable recommendation.

---

## Invocation

```
/finding [options]
```

### Options

| Option | Description | Example |
|--------|------------|---------|
| `--work-item <id>` | Link finding to a specific work item | `/finding --work-item WORK-001` |
| `--trace <id>` | Link finding to a trace result | `/finding --trace WORK-001` |
| `--audit <scope>` | Link finding to an audit report | `/finding --audit "mode=fix, last 30 days"` |
| (no options) | Create a standalone finding | `/finding` |

---

## Process

### Step 1 — Observation

State what you found. Be factual, not interpretive. Describe the condition, not the conclusion.

Ask yourself:
- What did you observe?
- Where did you observe it? (file, log entry, work item, phase)
- Is this a single occurrence or a pattern?

Write the observation in one to two sentences. Do not include your opinion of severity yet.

### Step 2 — Evidence

Provide specific, verifiable references that support the observation:

| Evidence type | Example |
|--------------|---------|
| File reference | `src/auth/middleware.ts:42` — missing null check |
| Log entry | `WORK-001.jsonl` line 15 — resolver self-resolved at 55% confidence (threshold 80%) |
| Test result | `npm test` — `auth.test.ts` 3 failures in session handling suite |
| Work item field | `WORK-003` brief missing acceptance criteria for error states |
| Diff reference | Commit `a1b2c3d` — removed input validation without replacement |
| Verification gap | AC3 in WORK-005 marked PASS with no evidence recorded |

A finding without evidence is not a finding. If you cannot point to a specific artifact, do not create the finding.

### Step 3 — Classify Severity

Apply the severity model from the investigation engine rules:

| Severity | When to use |
|----------|------------|
| **Critical** | Active defect, security vulnerability, or data loss risk. Requires immediate attention. |
| **Major** | Significant quality gap, pattern violation, or process failure. Needs action before next release. |
| **Minor** | Small quality issue, style inconsistency, or minor process deviation. Fix when convenient. |
| **Info** | Observation, suggestion, or positive pattern worth noting. No action required. |

Severity assignment rules:
- When in doubt between two levels, choose the higher severity.
- Security-related findings are never below Major.
- Data integrity findings are never below Major.
- Repeated Minor findings in the same area may warrant a Major finding for the pattern.

### Step 4 — Categorise

Assign one root cause category:

| Category | Description |
|----------|------------|
| **specification-gap** | Brief was incomplete or ambiguous. Acceptance criteria did not cover the requirement. |
| **implementation-error** | Agent produced incorrect output despite clear requirements. |
| **verification-miss** | Verifier passed something that should have failed, or missed a regression. |
| **escalation-failure** | Agent self-resolved when it should have escalated, or escalated unnecessarily. |
| **process-deviation** | A phase was skipped, a gate was not respected, or logging was incomplete. |
| **scope-creep** | Changes were made beyond what the brief and mode permitted. |
| **security-vulnerability** | A security weakness was introduced or left unaddressed. |
| **standards-violation** | Output does not meet the applicable quality standard (Craft, Safety, or Usability). |

### Step 5 — Recommend

Write a specific, actionable recommendation. Name the agent, template, process, or artefact that should change. Vague recommendations are not acceptable.

**Good:** "Update `backend-dev` specialist template to include rate-limiting guidance for API endpoints. Route to Profiling engine."

**Bad:** "Improve security practices."

Route the recommendation using the routing discipline:

| Finding scope | Route to |
|--------------|----------|
| Agent-specific code issue | The responsible specialist agent |
| Cross-agent pattern | Delivery engine (for process adjustment) |
| Standards gap | Profiling engine (for template update) |
| Process failure | Human reviewer |
| Security finding | security-audit agent AND human reviewer |

Critical findings always route to the human reviewer in addition to the technical recipient.

### Step 6 — Record the Finding

Add the finding to `findings.json` in the investigation engine's output directory. If the file does not exist, create it with an empty array and add the first entry.

#### findings.json Schema

```json
[
  {
    "id": "FINDING-001",
    "timestamp": "ISO-8601",
    "severity": "critical | major | minor | info",
    "category": "specification-gap | implementation-error | verification-miss | escalation-failure | process-deviation | scope-creep | security-vulnerability | standards-violation",
    "observation": "Factual description of what was found.",
    "evidence": [
      {
        "type": "file | log | test | work-item | diff | verification",
        "reference": "Specific location or identifier",
        "detail": "What the evidence shows"
      }
    ],
    "recommendation": "Specific action to take.",
    "route_to": "agent name | delivery-engine | profiling-engine | human-reviewer",
    "source": {
      "type": "trace | audit | manual",
      "reference": "WORK-001 | audit scope description"
    },
    "status": "open",
    "linked_work_items": ["WORK-001"],
    "resolution": null
  }
]
```

#### Required Fields

| Field | Type | Description |
|-------|------|------------|
| `id` | string | Unique finding ID. Auto-increment: FINDING-001, FINDING-002, etc. |
| `timestamp` | string | ISO-8601 creation timestamp. |
| `severity` | string | One of: critical, major, minor, info. |
| `category` | string | Root cause category from Step 4. |
| `observation` | string | Factual description (Step 1). |
| `evidence` | array | At least one evidence item (Step 2). |
| `recommendation` | string | Actionable recommendation (Step 5). |
| `route_to` | string | Recipient per routing discipline. |
| `source` | object | How this finding was discovered (trace, audit, or manual). |
| `status` | string | Current lifecycle status. Starts as "open". |

#### Optional Fields

| Field | Type | Description |
|-------|------|------------|
| `linked_work_items` | array | Work item IDs this finding relates to. |
| `resolution` | object | Populated when the finding is resolved. |

### Step 7 — Confirm Output

Present the finding summary:

```
FINDING: FINDING-003
Severity: major
Category: escalation-failure
Observation: backend-dev self-resolved a database migration decision at 55% confidence
             (Fix mode threshold: 80%).
Evidence:
  - Log: WORK-007.jsonl line 42 — resolver_decision, confidence=0.55, tier=self_resolve
  - Work item: WORK-007 — Fix mode, database schema migration
Recommendation: Review backend-dev confidence calibration for database operations.
                Route to delivery engine for threshold review.
Source: trace WORK-007
Status: open
```

---

## Finding Status Lifecycle

```
open → acknowledged → resolved → closed
```

| Status | Meaning | Who transitions |
|--------|---------|----------------|
| **open** | Finding created. Awaiting review. | Investigation engine (automatic on creation) |
| **acknowledged** | Recipient has seen the finding and accepted responsibility. | Routed recipient (agent or human) |
| **resolved** | The recommended action has been taken. Evidence of resolution provided. | Routed recipient |
| **closed** | Resolution verified. Finding archived. | Investigation engine (after verification) |

### Resolution Object

When a finding moves to "resolved", the recipient populates the resolution field:

```json
{
  "resolved_by": "agent name or human",
  "resolved_at": "ISO-8601",
  "action_taken": "Description of what was done",
  "evidence": "Reference to the fix — commit hash, updated template, etc."
}
```

The investigation engine verifies the resolution before transitioning to "closed". If the resolution is insufficient, the finding returns to "open" with a note.

---

## Read-Only Reminder

You are creating findings, not fixes. A finding describes what is wrong and recommends a course of action. You never implement the fix yourself. The delivery engine and its agents handle resolution.
