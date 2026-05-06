# Workflow Template

One workflow. Three modes. The mode shapes behaviour at every phase.

---

## Phases

Every work item follows the same five phases regardless of mode:

1. **Brief** — Capture what needs to happen. Agents apply the THINK sub-directives from Posture (Done State, Decision Authority, Assumption Risk) to surface gaps and assumptions, then resolve them with the human through the Resolution Protocol. Human approves the brief and Clarity Report.
2. **Self-Assess** — Each agent evaluates the brief against its specialty and declares involvement.
3. **Plan** — Involved agents produce an execution plan. Human approves.
4. **Execute** — Agents implement the plan. Peer consultation occurs here.
5. **Final Verify** — Every acceptance criterion gets explicit pass/fail with evidence. Human accepts.

---

## Modes

### Fix

**Purpose:** Restore correct behaviour.

**Brief questions:**
- What is the expected behaviour?
- What is the actual behaviour?
- When did it start? What changed?

**Flow:**
1. Capture symptoms from the brief, apply THINK sub-directives to assess clarity
2. Trace to root cause — identify why, not just where
3. Present root cause analysis to human
4. **Human decision point:** tactical fix (patch the symptom) or root cause fix (address the underlying issue)
5. Execute chosen approach
6. Verify the fix resolves the symptom AND does not introduce regressions

**Scope bias:** Conservative. Touch only what is necessary to restore correct behaviour.

**Resolver threshold:** 80% — do not make it worse.

**Verifier intensity:** Thorough at every phase.

---

### Change

**Purpose:** Evolve the codebase with new or modified functionality.

**Brief questions:**
- What is the requirement?
- What are the acceptance criteria?
- Are there patterns or conventions this must follow?

**Flow:**
1. Capture requirement and acceptance criteria, apply THINK sub-directives to assess clarity
2. Agents self-assess: who needs to be involved?
3. Plan: architecture approach, file changes, test strategy
4. Execute with peer feedback loops
5. Final verify against every acceptance criterion

**Scope bias:** Balanced. Full quality gates, pattern adherence, maintainability focus.

**Resolver threshold:** 60% — balanced autonomy for feature work.

**Verifier intensity:** Light on brief/plan, thorough on execute/final.

---

### Upgrade

**Purpose:** Technical platform migration. Zero business logic changes.

**Brief questions:**
- What is being upgraded? (framework, library, runtime)
- From which version to which version?
- What are the known breaking changes?

**Flow:**
1. Identify version diff and breaking changes, apply THINK sub-directives to assess clarity
2. Catalogue affected files and patterns
3. Execute migration — mechanical changes only
4. **Reclassify checkpoint:** If a change requires modifying business logic or test expectations, STOP. Reclassify the work item as **Change** mode. Upgrade mode permits only technical migration.
5. Run existing test suite — tests are the contract
6. Verify zero business logic changes

**Scope bias:** Strict. Existing tests are the contract. If test expectations must change, that signals a Change, not an Upgrade.

**Resolver threshold:** 80% — careful with compatibility.

**Verifier intensity:** Thorough at every phase.

---

## Agent Self-Selection

When a work item is briefed, each agent evaluates it against its specialty:

- **Lead** — This is my primary domain. I will plan and execute.
- **Support** — This touches my domain. I will review and consult.
- **Observe** — This does not touch my domain. I will not participate.

Not every agent participates in every work item. Self-selection prevents unnecessary context loading and noise.

---

## Human Gates

Three mandatory human checkpoints:

| Gate | When | Human decides |
|------|------|--------------|
| **After Brief** | Before planning begins | Approve scope, mode selection, Clarity Report resolutions, and agent involvement |
| **After Plan** | Before execution begins | Approve approach, file list, and test strategy |
| **After Final Verify** | Before work item closes | Accept delivery based on verification evidence |

The Brief gate includes the Clarity Assessment interaction — the human resolves Critical items through dialogue as part of the brief process, not as a separate checkpoint.

No work item progresses past a gate without explicit human approval.

---

## Urgency Modifier

Applied on top of any mode. Adjusts the Posture directives.

| Level | MINIMIZE effect | CUT effect | Human gates |
|-------|----------------|------------|-------------|
| **Normal** | Standard scope | Standard cleanup | All three gates |
| **Elevated** | Tighter scope — defer nice-to-haves | Aggressive — remove anything non-essential | All three gates |
| **Critical** | Minimum viable — fastest path to resolution | Maximum constraint | Brief gate may be expedited, plan/verify gates remain |

Urgency does not remove quality gates. It tightens scope to reach the goal faster.

---

## Peer Consultation During Execution

During the Execute phase, agents consult their structured pairs:

- Before making cross-boundary changes (e.g., frontend-dev modifying an API contract)
- When confidence drops below the mode's resolver threshold
- When a decision affects another agent's scope

Consultation is logged. The consulting agent retains decision ownership.
