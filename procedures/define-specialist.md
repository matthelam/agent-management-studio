# /define Command

Create a new specialist template or refine an existing one. Manage the promotion path from base-generated to catalogue-level specialist.

---

## Invocation

```
/define <specialist-name> [options]
```

### Options

| Option | Description | Example |
|--------|------------|---------|
| `--from-base` | Generate from the base template with guided input | `/define devops-engineer --from-base` |
| `--refine` | Load an existing specialist and improve it | `/define devops-engineer --refine` |
| `--promote` | Promote a mature specialist to the catalogue | `/define devops-engineer --promote` |
| `--configure` | Adjust mode settings for a project (thresholds, pairings) | `/define --configure` |
| (no options) | Create a new specialist interactively from scratch | `/define devops-engineer` |

---

## Process — Create New Specialist

### Step 1 — Name and Identity

Define the specialist's name and core identity:

- **Name:** A hyphenated lowercase identifier (e.g., `devops-engineer`, `data-analyst`, `mobile-dev`)
- **Identity:** One sentence describing what this specialist does and what it is responsible for

Example:
```markdown
# devops-engineer — Specialist

You are the DevOps engineer. You design and maintain CI/CD pipelines, infrastructure-as-code, and deployment automation.
```

### Step 2 — Scope

Define what the specialist does and does not do:

- **In scope:** The specific tasks and artefacts this specialist owns
- **Out of scope:** What this specialist must NOT do (prevents overlap with other specialists)
- **Output types:** What this specialist produces (code, configuration, scripts, reviews, etc.)

The output types determine which standards to load (Step 4).

### Step 3 — Version-Conditional Rules

If the specialist works with versioned technologies, define version-conditional rules:

```markdown
## Version-Conditional Rules

### Terraform
- **>= 1.5:** Use `import` blocks for state management. Use `check` blocks for assertions.
- **< 1.5:** Use `terraform import` CLI command. Use `precondition`/`postcondition` in lifecycle blocks.

### Kubernetes
- **>= 1.28:** Use sidecar containers as native init containers.
- **< 1.28:** Use init containers with shared volumes for sidecar patterns.
```

If the specialist is framework-agnostic (e.g., code-review), this section may be omitted.

### Step 4 — Standards References

Map the specialist to applicable standards based on output type:

| Output type | Standards to load |
|------------|------------------|
| Writes application code | Craft |
| Writes UI code or markup | Craft + Usability |
| Writes security-sensitive code | Craft + Safety |
| Reviews code (does not write) | Craft (as evaluation lens) |
| Audits security (does not write) | Safety (as evaluation lens) |
| Writes infrastructure/config only | Craft |

Select the minimum set. Do not load standards that are irrelevant to the specialist's output.

### Step 5 — Peer Pairing

Assign a default peer for structured consultation:

- The peer should have a complementary perspective (builder ↔ reviewer, implementer ↔ auditor)
- If no logical peer exists in the current catalogue, set to `null` and note that dynamic consultation is available via the resolver

Example:
```markdown
## Peer Pairing

Default peer: `security-audit`
Consultation topics: infrastructure security, access control, secrets management
```

### Step 6 — Boundaries

Define what the specialist must never do:

- Never take on work outside its scope
- Never modify artefacts owned by other specialists without peer consultation
- Never skip verification for its output type

### Step 7 — Validate and Save

**Validation checklist:**

| Check | Criteria |
|-------|---------|
| Identity | Clear, one-sentence role description |
| Scope | In-scope and out-of-scope defined, no overlap with existing specialists |
| Version rules | Present if specialist is version-dependent, omitted if framework-agnostic |
| Standards | Minimum relevant set selected, at least one standard referenced |
| Peer pairing | Logical peer assigned or explicitly set to null with justification |
| Boundaries | Clear prohibitions defined |
| Token budget | Total specialist template is 300-500 tokens |

**Human gate:** Present the complete specialist template to the human for review before saving.

Save to `agency/engines/profiling/templates/specialists/<name>.md`.

If this specialist was generated from the base template (via `/init` or `--from-base`), add a metadata comment at the top:

```markdown
<!-- generated: true | source: base-template | created: ISO-8601 -->
```

---

## Process — Refine Existing Specialist

Use `--refine` to improve an existing specialist based on usage experience.

### Step 1 — Load

Read the existing specialist template from `templates/specialists/<name>.md`.

### Step 2 — Review History

If investigation findings exist that reference this specialist, load them:
- What patterns were identified?
- What gaps were found?
- What recommendations were made?

### Step 3 — Identify Gaps

Compare the specialist against its usage history:
- Are version-conditional rules complete for the versions encountered?
- Is the scope still accurate? (Too broad? Too narrow?)
- Is the peer pairing effective?
- Are there recurring issues the specialist's template should address?

### Step 4 — Update

Apply targeted improvements. Follow the MINIMIZE posture directive — change only what needs changing.

### Step 5 — Validate and Save

Run the same validation checklist as new specialist creation (Step 7 above).

**Human gate:** Present the diff (what changed and why) to the human before saving.

---

## Process — Promote Specialist

Use `--promote` to elevate a base-generated specialist to the pre-built catalogue.

### Promotion Criteria

A specialist is ready for promotion when it meets ALL of the following:

| Criterion | How to verify |
|-----------|--------------|
| **Used in 3+ work items** | Check JSONL logs for agent participation |
| **No critical findings** | Check findings.json for critical/major findings referencing this specialist |
| **Version rules validated** | Version-conditional rules have been exercised against real code |
| **Peer pairing confirmed** | Peer consultation has occurred at least once with useful outcome |
| **Human-reviewed** | A human has reviewed the template at least once since last refinement |
| **Token budget met** | Template is within 300-500 tokens |

### Promotion Process

1. Verify all promotion criteria are met. If any fail, report which criteria are unmet and stop.
2. Remove the `<!-- generated: true -->` metadata comment.
3. Move the specialist from "generated" status to the pre-built catalogue.
4. Update any project `config.json` files that reference this specialist to mark it as `"generated": false`.

**Human gate:** Confirm promotion with the human.

```
PROMOTION: devops-engineer
Criteria met: ✓ 5/5 work items  ✓ No critical findings  ✓ Version rules validated
              ✓ Peer pairing confirmed  ✓ Human-reviewed  ✓ 420 tokens
Action: Promote to pre-built catalogue
```

---

## Process — Configure Mode Settings

Use `--configure` to adjust mode-specific settings for a project without creating or modifying specialists.

### Configurable Settings

| Setting | Default | Adjustable per project |
|---------|---------|----------------------|
| Fix mode resolver threshold | 80% | Yes — e.g., raise to 90% for safety-critical projects |
| Change mode resolver threshold | 60% | Yes — e.g., lower to 50% for rapid prototyping |
| Upgrade mode resolver threshold | 80% | Yes — e.g., raise to 90% for major version jumps |
| Peer pairings | Per specialist default | Yes — override for project-specific needs |
| Verifier intensity overrides | Per mode default | Yes — e.g., thorough everywhere for regulated projects |

### Configuration Process

1. Load the project's `config.json`.
2. Present current settings to the human.
3. Accept changes and validate (thresholds must be 0-100, pairings must reference valid specialists).
4. Save updated `config.json`.

**Human gate:** Confirm configuration changes before saving.

---

## Notes

- Every specialist template follows the same structure defined in `_base-template.md`.
- The token budget (300-500 tokens per specialist) ensures context efficiency.
- Promotion is a quality gate, not an automatic process. It requires evidence from real usage.
- Configuration changes affect the delivery engine's behaviour for the specific project only.
