# MCP Quality Harness

The criteria a candidate MCP must meet before being added to AMS's curated
registry. Applied by the `curate-mcp` skill. Codified in markdown so curators
have a single canonical reference.

This is the harness — the bar for what counts as a quality MCP that AMS will
recommend to target projects via `learn-codebase`'s ecosystem-discovery step.

---

## Quality dimensions

| # | Dimension | Type | Hard / Soft |
|---|---|---|---|
| 1 | Provenance | manual confirmation | **Hard** |
| 2 | Maintenance health | automated check | **Hard** |
| 3 | Distribution | automated + manual | **Hard** |
| 4 | Documentation | automated + manual | **Hard** |
| 5 | Stability | manual scoring | Soft |
| 6 | Security posture | manual review | **Hard** |
| 7 | CRUD truthfulness | manual review per method | **Hard** |
| 8 | License | automated check | **Hard** |
| 9 | Auth model | manual review | **Hard** |
| 10 | Functional fit | manual scoring | Soft |

Hard dimensions: a fail blocks approval. Soft dimensions: scored and recorded;
inform "conditional" verdict.

---

## 1. Provenance

**Question:** Is this MCP actually from the vendor whose technology it manages?

**Auto-check signals:**
- npm: package owner matches expected org for the tech
- github: org name matches vendor (e.g. `vercel/`, `microsoft/`, `anthropics/`)
- Domain: project URL on a domain owned by the vendor

**Manual confirmation:**
- Check the vendor's official documentation for a list of supported MCPs
- If the candidate isn't in the vendor's official list, it's a community MCP —
  acceptable but flag in the catalogue

**Pass:** vendor-authentic OR community-authentic with the maintainer's
identity verifiable via GitHub profile + at least one verifiable other
project from the same author.

**Fail:** A brand name (e.g. "azure-mcp") published by an unrelated user with
no other verifiable presence.

---

## 2. Maintenance health

**Question:** Is this MCP actively maintained?

**Auto-check signals:**
- `pushedAt` (latest commit date)
- Release/tag cadence over last 365 days
- Open issue count + time-to-first-response on recent issues

**Bands:**
- < 90 days since last commit → **active**
- 90-365 days → **stale-warning** (conditional approval; caveat in catalogue)
- \> 365 days → **stale-fail** (reject unless special-case override)

---

## 3. Distribution

**Question:** Can target projects install this without exotic procedures?

**Pass criteria (any one):**
- Published to npm with install command available
- Available via Claude Code plugin marketplace
- Hosted MCP with documented connection instructions
- Docker image with documented `docker run` command

**Fail:** Source-only with bespoke build steps required, or no install path
documented at all.

---

## 4. Documentation

**Question:** Is the MCP usable from its docs alone?

**Pass criteria:**
- README with non-trivial content (more than just a title)
- Tool/method list documented (either in README or via `tools/list` MCP method)
- Required configuration documented
- At least one usage example

**Fail:** Empty README, no tool list, no usage examples.

---

## 5. Stability

**Scoring 1-5:**
- 5: SemVer; documented breaking-change policy; changelog
- 4: SemVer; informal changelog
- 3: Versioning present; no formal policy
- 2: Versioning sporadic
- 1: No versioning; breaking changes without notice

---

## 6. Security posture

**Manual review:**
- Does the MCP request credentials only for declared operations?
- Are unauthorized network calls absent? (Spot-check the source for outbound HTTP)
- Is credential handling secure? (env vars / OS keychain, not hardcoded)
- Does the MCP run untrusted user-provided strings as commands? (e.g.
  `eval`-style)

**Hard fail** on any of: credential exfiltration, hardcoded secrets,
unsanitized command execution, undocumented telemetry to third parties.

---

## 7. CRUD truthfulness

**Per method:**

For each method the MCP exposes, classify accurately:

| Class | Definition |
|---|---|
| `pure-read` | No side effects of any kind |
| `read-with-side-effects` | Documented as read but writes logs, telemetry, mtime, cache, lock files, etc. |
| `write` | Modifies state in local repo or remote system |
| `destructive` | Irreversible (deletions, force-pushes, drops) |

**Hard requirement:** Every method must be classified. `read-with-side-effects`
classifications must list the specific side effects.

**Why this matters:** target projects' `tool-safety` skill uses this data to
enforce "read-only really means read-only" in audit/investigation modes.
Misclassification breaks that guarantee.

---

## 8. License

**Allowed:**
- MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC, MPL-2.0

**Forbidden:**
- GPL-2.0, GPL-3.0, AGPL-3.0 (incompatible with closed-source AMS-managed projects)
- Custom restrictive licenses
- Unlicensed (= all rights reserved)

**Conditional (case-by-case):**
- LGPL — usually OK for libraries, ask the curator
- BUSL — depends on the use case
- Proprietary commercial — acceptable if the project's license allows it

---

## 9. Auth model

**Review:**
- OAuth / SSO / passwordless: preferred
- API key in env var: acceptable
- API key via credentials file: acceptable
- API key passed as CLI arg: acceptable but warn (history exposure)
- Hardcoded credentials in source: **fail**
- No auth (public API): acceptable for read-only public APIs

---

## 10. Functional fit

**Scoring 1-5:**
- 5: Covers the most common 90%+ use cases for the technology
- 4: Covers core use cases; missing some advanced ones
- 3: Covers basic use cases; significant gaps
- 2: Covers narrow slice
- 1: Toy implementation; not production-viable

Functional fit is per-technology. The same MCP may score 5 for one tech and
3 for another.

---

## Verdicts

After scoring all dimensions:

| All hards pass + soft scores ≥3 | **Approved** — add to catalogue without caveat |
| All hards pass + soft scores mixed | **Approved (conditional)** — add with explicit caveat in catalogue notes |
| Any hard fails | **Rejected** — do not add; document reason for future curator reference |

---

## Re-evaluation cadence

Approved MCPs should be re-evaluated:
- Annually at minimum
- When a new major version is released
- When a security advisory is reported against the MCP or its dependencies
- When real-world usage in target projects surfaces issues

Re-evaluation findings update the catalogue entry's `harness.scored_at` and
verdict.
