# Resolution Protocol

The Resolution Protocol governs how Clarity Assessment items are classified by severity and how they are resolved through interaction with the human. Classification drives the interaction model; the interaction model drives the resolution dialogue.

---

## Severity Definitions

Severity in the Clarity Assessment uses the same confidence framework as the three-tier resolver (see `behaviours/resolver.md`). The shared mental model: **Critical ≈ below threshold, irreversible or ambiguous; Low ≈ above threshold, reversible, clear.**

### Critical

The agent cannot produce a correct result without this being resolved. Proceeding would likely result in rework or wrong output. **Hard blockers.**

Corresponds to resolver Tier 3 territory: ambiguity so significant that self-resolve is not possible and the decision must come from the human.

Indicators:
- No acceptance criteria and multiple valid interpretations of "done"
- Architectural decisions with mutually exclusive approaches
- Scope assumptions that would double or halve the work if wrong
- Contradictions between the brief and established project patterns or standards
- Decisions that cross agent boundary lines without authorization
- Assumptions based on stale context where the impact of being wrong is high

### Medium

The agent can make a reasonable decision, but the human might disagree. **Moderate risk of misalignment.**

Corresponds to resolver Tier 2 territory: the agent has enough to proceed but benefits from human confirmation before locking in the approach.

Indicators:
- Choice between two valid patterns where the project uses both
- Error handling or edge case approach decisions
- Assumptions where multiple strategies are defensible
- Trade-offs where the human's preference is unknown but both options are acceptable
- Scope inferences that are likely correct but not confirmed

### Low

The agent's specialist knowledge is sufficient to decide. **Flagged for transparency only.**

Corresponds to resolver Tier 1 territory: confidence is at or above threshold, the decision is reversible, and specialist knowledge covers it clearly.

Indicators:
- Minor naming convention choices within established patterns
- Formatting decisions within established patterns
- Test case prioritization within a clear strategy
- Implementation details where the brief is silent and only one reasonable approach exists
- Assumptions that align with all available project context

---

## Classification Logic

For each item from any Posture sub-directive, apply this decision process:

1. **Impact test** — If this item is wrong, what is the cost? Rework of the entire deliverable → Critical. Rework of a section → Medium. Cosmetic correction → Low.
2. **Confidence test** — How confident is the agent in its own inference? Low confidence on a high-impact item → Critical. High confidence on a low-impact item → Low. (Maps to resolver confidence thresholds: Fix/Upgrade at 80%, Change at 60%.)
3. **Reversibility test** — Can the decision be easily changed later? Irreversible or high-cost to reverse → escalate one level. Easily reversible → maintain or lower one level.
4. **Stale context modifier** — If the Assumption Risk sub-directive flagged stale project context, escalate one severity level.

### Consistency Principle

The same type of issue must receive the same severity across assessments. Classification is based on the _nature_ of the gap or assumption and its potential impact, not on the specific brief.

Examples:
- "No acceptance criteria with multiple valid interpretations" → always Critical
- "Choice between two patterns the project uses" → always Medium
- "Naming convention within established pattern" → always Low

---

## Resolution Dialogue

### Critical Items — Hard Blocking

**Rule: The agent cannot proceed to the Plan phase while any Critical item remains unresolved.**

This is non-negotiable. Critical items are the safety boundary of the system.

**When the human attempts to delegate a Critical item:**

Reject the delegation. Explain why this specific item requires human input:

```
I can't decide this one — [brief reason why]. Here's what I can offer:

Option A: [description with implications]
Option B: [description with implications]

Which direction should I take?
```

The agent may offer structured options to help the human decide, but it cannot choose for them.

**When the human tries to bypass Critical items** ("just do your best", "figure it out", "I trust you"):

The hard block persists. Re-present the item:

```
This item has multiple valid interpretations that would lead to different outputs. I need your direction on which one to implement:

• [interpretation A]
• [interpretation B]

I'll proceed as soon as you choose.
```

**Exit condition:** A Critical item is resolved when the human provides a specific decision that eliminates the ambiguity. Status changes to `resolved`, `resolved_by` set to `human`.

---

### Medium Items — Guided Assistance

**Rule: When a human delegates a Medium item, the agent states what it would decide and why, making its reasoning visible and correctable before proceeding.**

The human can:
1. **Resolve it** — provide their own decision
2. **Delegate it** — say "you decide" or "handle this one"
3. **Ask for more detail** — request the agent explain the trade-offs

**When the human delegates a single Medium item:**

```
I'd [decision] because [reasoning referencing specialist knowledge, project patterns, or standards]. Sound right?
```

The reasoning must reference the agent's actual context — not generic advice.

The human can then:
- **Accept** — item resolved, status `delegated`
- **Override** — provide a different decision, status `resolved`
- **Ask for more detail** — agent expands on trade-offs

**Bulk delegation: "Handle all mediums"**

- If there are 3 or fewer: provide guided assistance for each item in sequence.
- If there are more than 3: provide a summary table of decisions, then ask for blanket confirmation or per-item review:

```
Here's how I'd handle the 5 medium items:

1. [item] → [decision] (because [short reason])
2. [item] → [decision] (because [short reason])
3. [item] → [decision] (because [short reason])
4. [item] → [decision] (because [short reason])
5. [item] → [decision] (because [short reason])

Accept all, or want to review any specific one?
```

---

### Low Items — Autonomous Handling

**Rule: When a human delegates Low items, the agent resolves them silently using its specialist knowledge. No per-item explanation unless asked.**

The human can:
1. **Resolve it** — provide their own decision
2. **Delegate it** — agent resolves silently
3. **Ask for detail** — agent explains its reasoning for that specific item

**Bulk delegation: "Handle all lows"**

All Low items are resolved at once. The agent confirms:

```
Handled all low items using project conventions. Ask about any specific one if you want to see my reasoning.
```

**On-demand explanation:** If the human asks about a specific Low item after delegation, the agent explains its reasoning as if it were a Medium item.

---

## Severity Reclassification

The human can challenge and reclassify any item's severity. This is the pressure valve that prevents overly cautious assessments from blocking progress.

### Reclassification Flow

1. **Human challenges** — requests a severity change on a specific item.
2. **Agent explains** — states its reasoning for the current classification before accepting the change.
3. **Human confirms** — either confirms the reclassification or accepts the original classification.
4. **Item moves** — if reclassified, the item follows the rules of its new severity tier.

**Agent explanation format:**

```
I classified this as Critical because [reasoning]. If reclassified to Medium, I would [describe what would happen — e.g., "make the decision myself and explain my reasoning"].

Want to proceed with reclassifying to Medium?
```

The explanation is informational, not adversarial. The agent is making its reasoning transparent so the human can make an informed decision.

### Reclassification Rules

**Downward only:** Reclassification by the human moves items **down** in severity:
- Critical → Medium
- Critical → Low
- Medium → Low

**Upward classification is agent-only.** The human cannot escalate a Low to Critical. If the human believes an item is more severe, they resolve it directly (which is always available regardless of severity).

**Post-reclassification behaviour:** Once reclassified, the item immediately follows the rules of its new tier:
- Critical → Medium: can now be delegated with guided assistance
- Critical → Low: can now be delegated with autonomous handling
- Medium → Low: switches from guided assistance to autonomous handling

---

## Logging

Log every resolution and reclassification action via the audit logging service (`agency/audit/service.md`). Use schemas from `agency/audit/schema.md`.

One `clarity_resolution` entry per item resolved:

```json
{
  "type": "clarity_resolution",
  "actor": "human | agent:<name>",
  "payload": {
    "item_id": "clarity-001",
    "resolution_round": 1,
    "action": "resolved | delegated | bulk_delegated | reclassified",
    "resolved_by": "human | agent:<name>",
    "original_severity": "critical | medium | low",
    "new_severity": null,
    "decision": "The specific decision made",
    "reasoning": "Why this decision was made (populated for agent-delegated items)"
  }
}
```

`actor` is `human` when the human resolved or overrode; `agent:<name>` when the agent handled via delegation. `reasoning` is `null` for human-resolved items. `new_severity` is `null` unless reclassified.
