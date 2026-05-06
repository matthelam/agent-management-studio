---
name: accessibility-lens
description: Overlay applied on top of any harness. Adds accessibility-focused review concerns — WCAG conformance, keyboard navigation, screen reader behaviour, contrast, semantic HTML, focus management. Always-on for UI-heavy work; can be requested ad-hoc.
applies_on_top_of: any_harness
---

# Accessibility Lens

Overlay that augments any harness with accessibility-specific review concerns.

## Concerns surfaced

- **Perceivability** — text alternatives for images; sufficient contrast
  (WCAG AA: 4.5:1 normal, 3:1 large); no information conveyed via colour
  alone; resizable text.
- **Operability** — keyboard accessibility on every interactive element;
  logical focus order; visible focus indicators; no keyboard traps; skip
  links for repeated nav.
- **Understandability** — clear labels and instructions; specific error
  messages identifying the field and problem; consistent navigation; clear
  page titles.
- **Robustness** — semantic HTML preferred over `div`/`span`; ARIA only
  where semantic HTML insufficient; valid HTML; compatibility with assistive
  tech (screen readers, magnifiers, voice control).
- **Focus management** — modals trap focus correctly; focus returns to
  trigger on close; route changes update focus.
- **Status announcements** — `aria-live` regions for dynamic content;
  non-visual feedback for actions taken.

## Prompt overlay

Append to the harness's posture_anchor:

> *In addition to your primary lens, evaluate every UI claim against these
> accessibility concerns: perceivability (contrast, text alternatives),
> operability (keyboard, focus), understandability (labels, errors),
> robustness (semantic HTML, ARIA correctness), focus management,
> status announcements. Conformance target is WCAG 2.2 AA unless the project
> declares otherwise. Flag any non-semantic element used where a semantic one
> exists. Flag any interactive element without a visible focus indicator.*

## Combinations

- **Specifist + Accessibility** — exhaustive WCAG conformance check on every
  interactive element.
- **Architect + Accessibility** — structural accessibility review (e.g.,
  routing patterns that break focus management).
- **Empiricist + Accessibility** — cite the specific element, attribute, or
  contrast value.

## Default-on triggers

The Accessibility lens is always-on when:
- The project's `assembly.default_lenses` includes `accessibility`
- The current work touches UI components, forms, navigation, modals, or
  any interactive element
- The dev's prompt mentions accessibility, a11y, WCAG, screen reader,
  keyboard nav, contrast

## Routing implication

Findings produced under the Accessibility lens route to:
- `accessibility-audit` specialist (if present in project assembly)
- `frontend-dev` specialist (if not)
- AND human reviewer for any Critical accessibility violations
