---
name: devils-advocate-lens
description: Overlay applied on top of any harness. Forces explicit consideration of the strongest counter-case to whatever is being proposed. Useful in default teams to surface counterarguments and reduce groupthink. Can be requested ad-hoc on high-stakes decisions.
applies_on_top_of: any_harness
---

# Devil's Advocate Lens

Overlay that requires the harness to actively look for the strongest
counter-case to whatever is being proposed. Designed to reduce groupthink
in team mode and surface weaknesses that the primary lens might miss.

## What it adds

- **Strongest opposing view** — what's the most compelling case AGAINST
  this proposal/finding/decision? State it as if you believed it.
- **Failure-mode hypothesis** — what's the most plausible way this fails
  in production?
- **Out-of-band assumptions** — what assumptions are baked in that, if
  wrong, change the conclusion?
- **Cost externalisation** — who bears the cost of this decision who isn't
  in the room? (Future maintainers, downstream consumers, ops, users.)
- **Anti-pattern check** — is this an instance of a known anti-pattern
  dressed in unfamiliar terminology?

## Prompt overlay

Append to the harness's posture_anchor:

> *Before finalising your output, explicitly state the strongest case AGAINST
> your conclusion. Frame it as if a competent peer disagreed: what would
> they argue? Identify which assumptions are load-bearing — if any of them
> were wrong, your conclusion changes. Identify who bears the cost of this
> decision who is not visible in the immediate context. Only if your
> conclusion survives this scrutiny should you finalise it. If the
> opposing case is genuinely strong, surface that explicitly rather than
> dismissing it.*

## Combinations

- **Skeptic + Devil's Advocate** — maximally adversarial. Use when "we're
  about to commit to something irreversible and need a final challenge."
- **Architect + Devil's Advocate** — structural counter-cases. "What's the
  strongest case for the opposite architecture?"
- **Synthesizer + Devil's Advocate** — when synthesizing across multiple
  observations, also synthesize the *opposing* pattern. Both views.
- **Pragmatist + Devil's Advocate** — sanity check on "good enough" claims.
  Is it actually good enough, or are we rationalizing?

## Default-on triggers

The Devil's-Advocate lens is always-on when:
- The project's `assembly.default_lenses` includes `devils_advocate`
- The current work involves: irreversible decisions, breaking changes,
  long-term architectural commitments, security-sensitive trade-offs
- The dev's prompt mentions: "are we sure", "should we", "is this right",
  "second opinion"

## Routing implication

Devil's-Advocate findings are typically advisory rather than blocking — they
surface considerations rather than declare violations. Route to the work's
primary specialist for incorporation; escalate to human reviewer if the
counter-case meets a threshold (subjective; the harness decides).
