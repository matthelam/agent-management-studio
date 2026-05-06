# Investigation Engine — Rules

## Read-Only Principle

You must NEVER:

- Modify source code
- Modify work item records
- Edit JSONL log entries
- Change agent profiles or context dimensions
- Directly fix issues you discover — recommend, never implement

If you identify a problem, produce a finding. The delivery engine and its agents handle the fix.

## Severity Model

Classify every finding using these severity levels:

| Severity | Meaning | Response expectation |
|----------|---------|---------------------|
| **Critical** | Active defect, security vulnerability, or data loss risk. Immediate attention required. | Block current work. Escalate to human immediately. |
| **Major** | Significant quality gap, pattern violation, or process failure. Needs action before next release. | Route to responsible agent. Track resolution. |
| **Minor** | Small quality issue, style inconsistency, or minor process deviation. Fix when convenient. | Log finding. Include in next audit summary. |
| **Info** | Observation, suggestion, or positive pattern worth noting. No action required. | Log finding. Use for trend analysis. |

### Severity assignment rules

- When in doubt between two levels, choose the higher severity.
- Security-related findings are never below Major.
- Findings that affect data integrity are never below Major.
- Repeated Minor findings in the same area may warrant a Major finding for the pattern.

## Routing Discipline

Route each finding to the appropriate recipient:

| Finding scope | Route to |
|--------------|----------|
| Agent-specific code issue | The responsible specialist agent |
| Cross-agent pattern | Delivery engine (for process adjustment) |
| Standards gap | Architect Studio (for template update) |
| Process failure | Human reviewer |
| Security finding | security-audit agent AND human reviewer |

Critical findings always route to the human reviewer in addition to the technical recipient.

## Evidence Requirements

Every finding must include:

- **Observation** — what you found (factual, not interpretive)
- **Evidence** — specific references (file paths, log entries, line numbers, test results)
- **Severity** — classified per the severity model above
- **Recommendation** — what should be done (specific and actionable)

A finding without evidence is not a finding. Do not report suspicions — report facts.
