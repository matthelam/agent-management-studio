# Tool Quality Harness

The criteria any tool candidate must meet before being added to AMS's curated
registry. Applied by the `curate-tool` skill.

A "tool" is any artefact that harnesses AI development: MCPs (live system
access), skill packs (domain knowledge), or agent configs (cognitive shape).
The harness question for every candidate is the same:

> **Does this reduce AI guesswork and constrain it to correct,
> project-specific behaviour — without adding more friction than it saves?**

---

## Tool types

| Type | What it does | Harness mechanism |
|---|---|---|
| `mcp` | Connects AI to live system state | Real data replaces AI guessing |
| `skill-pack` | Domain knowledge docs | Constrains AI to correct SDK/framework patterns |
| `agent-config` | Cognitive team shape, guard rails, personas | Controls how AI reasons |

Each type has type-specific evaluation notes below (§11). The core dimensions
(1–10) apply to all types.

---

## Quality dimensions

| # | Dimension | Type | Hard / Soft |
|---|---|---|---|
| 1 | Provenance | manual confirmation | **Hard** |
| 2 | Harness strength | manual scoring | **Hard** |
| 3 | Domain depth | manual scoring | Soft |
| 4 | Accuracy risk | manual review | **Hard** |
| 5 | Friction cost | manual scoring | Soft |
| 6 | Composability | manual review | Soft |
| 7 | Security posture | manual review | **Hard** |
| 8 | CRUD truthfulness | manual review per method (MCPs only) | **Hard** (MCPs) |
| 9 | License | automated check | **Hard** |
| 10 | Auth model | manual review | **Hard** |

Hard dimensions: a fail blocks approval. Soft dimensions: scored and recorded;
inform "conditional" verdict.

---

## 1. Provenance

**Question:** Is this tool actually from the vendor whose technology it covers?

**Auto-check signals:**
- npm: package owner matches expected org
- github: org matches vendor (`vercel/`, `microsoft/`, `shadcn-ui/`)
- Domain: project URL on a vendor-owned domain

**Manual confirmation:**
- Check vendor's official docs/site for a mention of this tool
- Community tools: acceptable if maintainer identity is verifiable (GitHub
  profile, other verifiable projects, active issue response)

**Pass:** Vendor-authentic OR community-authentic with verifiable maintainer.

**Fail:** Brand name (e.g. "azure-tool") from an unrelated user with no
verifiable identity or track record.

---

## 2. Harness strength

**Question:** Does this tool actively constrain or guide AI to correct
behaviour — or does it merely inform?

**Scoring 1-5:**
- 5: Hard constraints — blocks incorrect patterns, enforces specific APIs/paths
- 4: Strong guidance — project-specific patterns with examples + anti-examples
- 3: Domain reference — correct patterns documented but no constraint mechanism
- 2: Generic guidance — not specific to this project/version
- 1: Marketing copy — surface-level; adds noise not signal

**Hard minimum:** Score ≥ 2. Score 1 = reject.

**Why this matters:** A tool that's merely informative adds context window
cost without improving correctness. The bar is "does AI make fewer mistakes
with this loaded?"

---

## 3. Domain depth

**Question:** How much project-specific knowledge does this tool encode?

**Scoring 1-5:**
- 5: Version-pinned, project-specific patterns with concrete examples
- 4: Framework-specific with version awareness
- 3: Framework-specific, version-agnostic
- 2: General-purpose with some domain coverage
- 1: Generic

---

## 4. Accuracy risk

**Question:** Can this tool mislead AI into incorrect behaviour?

**Sources of accuracy risk:**
- Stale documentation (out of date vs. current library version)
- Incorrect CRUD classification (read methods with hidden side effects)
- Aspirational descriptions that don't match actual behaviour
- Community tools with unverified claims

**Hard fail on any of:**
- Known documentation that contradicts current library behaviour
- MCP methods documented as read-only that demonstrably write state
- Skill pack recommending deprecated patterns as current

**Pass:** Accuracy risks identified and documented in catalogue; caveat in notes.

---

## 5. Friction cost

**Question:** How much setup and ongoing maintenance does this tool require?

**Scoring 1-5 (lower = more friction):**
- 5: Zero-config; auto-discovered or hosted; no maintenance
- 4: One-time config (env var, API key); no ongoing maintenance
- 3: Per-project setup; infrequent updates needed
- 2: Non-trivial setup; manual version tracking required
- 1: Heavy setup; breaks regularly; high maintenance burden

---

## 6. Composability

**Question:** Does this tool layer cleanly with other tools in the AMS stack?

**Review:**
- Does it duplicate coverage of another curated tool? (overlap = caveat)
- Does it conflict with guard rails or prescriptive rules?
- For MCPs: does it expose methods that overlap with CLI tools already in scope?
- For skill packs: does it contradict patterns in the project's patterns.md?

**Soft fail:** Significant overlap with existing tool → document and let
curator decide priority.

---

## 7. Security posture

**Manual review:**
- Does the tool request credentials only for declared operations?
- Are unauthorized network calls absent?
- Is credential handling secure (env vars / keychain, not hardcoded)?
- For skill packs: does it recommend insecure patterns (e.g. disabling auth,
  storing secrets in code)?

**Hard fail:** Credential exfiltration, hardcoded secrets, unsanitized command
execution, undocumented telemetry to third parties, recommending insecure patterns.

---

## 8. CRUD truthfulness (MCPs only)

Per method, classify accurately:

| Class | Definition |
|---|---|
| `pure-read` | No side effects of any kind |
| `read-with-side-effects` | Documented as read but writes logs, telemetry, mtime, cache, lock files, etc. |
| `write` | Modifies state in local repo or remote system |
| `destructive` | Irreversible (deletions, force-pushes, drops) |

**Hard requirement (MCPs):** Every method must be classified. Side effects for
`read-with-side-effects` must be explicitly listed.

Not applicable to skill packs or agent configs.

---

## 9. License

**Allowed:** MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC, MPL-2.0

**Forbidden:** GPL-2.0, GPL-3.0, AGPL-3.0, custom restrictive, unlicensed

**Conditional (case-by-case):** LGPL, BUSL, proprietary commercial

For hosted MCPs with no local install: licence may be N/A — document as
"hosted-saas" and note ToS review required instead.

---

## 10. Auth model

- OAuth / SSO / passwordless: preferred
- API key in env var: acceptable
- API key via credentials file: acceptable
- API key passed as CLI arg: acceptable but warn (history exposure)
- Hardcoded credentials: **fail**
- No auth (public API or local tool): acceptable

---

## 11. Type-specific notes

### MCP-specific
- Enumerate the full method list; CRUD-classify every method (§8)
- Verify the MCP is reachable and returns a valid `tools/list` response
- Note if the MCP is local-process (security boundary = local) vs hosted
  (security boundary = network + auth)
- Maintenance health: last commit < 90 days = active; 90-365 = stale-warning;
  > 365 = stale-fail (unless hosted with active SLA)

### Skill-pack-specific
- Identify individual skills within the pack; note which are project-relevant
- Check version alignment: does the skill reference library versions that
  match the target project's lockfile?
- Identify the ingestion path: copy individual SKILL.md files vs. reference
  the pack as a source

### Agent-config-specific
- Review cognitive team composition for blind spots (e.g. no security lens
  on a security-sensitive project)
- Check guard rails for conflicts with project's prescriptive-rules.json
- Verify persona descriptions are concrete, not aspirational

---

## 12. Gap analysis (mandatory)

During curation, if the tool being evaluated leaves a harness gap — i.e. it
informs AI but doesn't fully constrain it to correct patterns for a concern —
the curator **must** identify and evaluate a complementary tool to patch that gap.

**Process:**
1. After scoring §2 (harness strength), identify any coverage gaps
2. For each gap, search for a complementary tool (MCP, skill, guard rail, or
   domain knowledge file) that would close it
3. If a viable candidate is found, initiate a curation run for it immediately
   (or queue it with a `gap_for` reference in the catalogue)
4. If no tool exists, note the gap in the catalogue entry's `harness.notes`
   so learn-codebase can generate a compensating domain skill instead

**Example:** shadcn MCP installs components but doesn't teach AI *how* to use
them correctly in a CVA/Radix pattern. The gap → a shadcn-specific skill or
the tailwind-radix domain skill must be confirmed present before the MCP is
marked fully effective.

Gap findings are recorded in the catalogue entry under `harness.gaps`.

---

## Verdicts

| Condition | Verdict |
|---|---|
| All hards pass + soft scores ≥ 3 | **Approved** — add to catalogue without caveat |
| All hards pass + soft scores mixed | **Approved (conditional)** — add with explicit caveat |
| Any hard fails | **Rejected** — document reason for future curator reference |

---

## Re-evaluation cadence

All curated tools should be re-evaluated:
- Annually at minimum
- When a new major version is released
- When a security advisory is reported
- When real-world usage in target projects surfaces issues
- When a skill pack's referenced library version diverges significantly from
  projects using it

Re-evaluation updates `harness.scored_at` and verdict in tool-catalogue.json.
