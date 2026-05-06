---
name: security-lens
description: Overlay applied on top of any harness. Adds security-focused review concerns — injection surfaces, auth boundaries, secrets handling, privilege escalation, data exposure. Always-on for security-sensitive code; can be requested ad-hoc via natural language.
applies_on_top_of: any_harness
---

# Security Lens

Overlay that augments any harness with security-specific review concerns.
The harness provides cognitive style; the lens narrows attention to security
dimensions.

## Concerns surfaced

- **Injection surfaces** — SQL injection, XSS, command injection, template
  injection, prompt injection in LLM workflows.
- **Auth boundaries** — where authentication is enforced, where it's bypassed,
  where session validity is assumed.
- **Secrets handling** — what's logged, what's serialised, what's committed,
  what's transmitted; rotation surfaces.
- **Privilege escalation paths** — where a low-privilege caller could obtain
  high-privilege effects.
- **Data exposure** — PII, payment data, internal identifiers, error messages
  that leak structure.
- **Trust boundaries** — server-side enforcement of client-supplied invariants;
  external service trust assumptions.
- **Dependency surfaces** — upstream packages with known CVEs; supply-chain
  signals.

## Prompt overlay

Append to the harness's posture_anchor:

> *In addition to your primary lens, evaluate every claim against these
> security concerns: injection surfaces, auth boundaries, secrets handling,
> privilege escalation paths, data exposure, trust boundaries, dependency
> CVEs. Flag explicitly when a security implication is out of scope but
> worth raising. Security findings are never below Major severity per the
> investigation rules.*

## Combinations

- **Skeptic + Security** — adversarial security review. Find what could
  exploit this code.
- **Architect + Security** — secure-by-design review. Find structural
  vulnerabilities (e.g., trust crossings without enforcement).
- **Empiricist + Security** — evidence-driven security audit. Cite the
  specific request flow that exposes the surface.
- **Specifist + Security** — exhaustive enumeration of concrete attack
  surfaces (every input boundary, every output boundary).

## Default-on triggers

The Security lens is always-on when:
- The project's `assembly.default_lenses` includes `security`
- The current work touches any of: auth, payments, data storage, external
  inputs, secrets, network boundaries
- The dev's prompt mentions security, vulnerability, audit, or
  authentication-related terms

## Routing implication

Findings produced under the Security lens are always routed to:
- The relevant specialist agent (e.g., `security-audit`, `backend-dev`)
- AND the human reviewer (per investigation-rules routing discipline)
