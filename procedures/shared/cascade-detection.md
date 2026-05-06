# Cascade Detection for Related Changes

Detect when multiple environment changes are inherently linked and present them as grouped events in the review gate rather than isolated changes.

---

## Purpose

Some changes travel together. Migrating from Jest to Vitest isn't just a test runner swap — it means mock patterns change, config files change, and runner commands change. Presenting these as three separate review items obscures the fact that they're one logical decision. Cascade detection groups them.

---

## Known Cascade Patterns

| Cascade Trigger | Related Changes | Rationale |
|----------------|-----------------|-----------|
| **Framework + Router** | Next.js major bump → `structure.src_layout` change (pages/ → app/) | App Router migration is tied to the Next.js version |
| **Test Runner + Mocking** | Jest → Vitest → mock pattern changes, config file changes | Vitest uses a different mock API and config format |
| **TypeScript Major** | TypeScript bump → linting rule changes, build config changes | TSConfig strictness and ESLint TS rules are coupled |
| **CSS Framework** | Tailwind major bump → PostCSS config, utility class changes | Tailwind versions change available utilities and config format |
| **Runtime + Native APIs** | Node.js major bump → native fetch availability, test runner availability | Node 18+ has native fetch; Node 22+ has stable test runner |
| **Framework + Meta-Framework** | React major bump + Next.js bump when both change | React version determines which Next.js features are available |
| **ORM + Database** | Prisma major bump → schema syntax changes, migration format changes | ORM migrations are tightly coupled to ORM version |
| **Linter + Formatter** | ESLint major bump → plugin compatibility, config format (flat config) | ESLint 9 moved to flat config, breaking most plugin configs |

---

## Process

### Step 1 — Scan for Cascade Patterns

After the change-to-agent resolution produces its list of proposed updates, scan for known cascade patterns:

1. For each change in the diff report, check if it matches a cascade trigger
2. If a trigger matches, look for the related changes in the same diff report
3. If related changes are present, group them into a cascade

### Step 2 — Build Cascade Groups

A cascade group contains:

```json
{
  "cascade": {
    "trigger": "next",
    "trigger_change": "14.1.0 → 15.0.0",
    "name": "Next.js 15 Migration",
    "related_changes": [
      { "key": "next", "change": "14.1.0 → 15.0.0" },
      { "key": "structure.src_layout", "change": "pages-router → app-router" },
      { "key": "react", "change": "18.2.0 → 19.0.0" }
    ],
    "affected_agents": ["frontend-dev", "code-review"],
    "combined_impact": "major"
  }
}
```

The cascade's `combined_impact` is the highest impact level among its constituent changes.

### Step 3 — Present as Grouped Review Item

In the human review gate, cascades are presented as a single item with expandable sub-items:

```
[1/3] 🔴 MAJOR CASCADE — Next.js 15 Migration
  Grouped changes:
    - next: 14.1.0 → 15.0.0
    - structure.src_layout: pages-router → app-router
    - react: 18.2.0 → 19.0.0
  Affects: frontend-dev, code-review

  Action: [Review all] [Approve cascade] [Review individually] [Defer cascade]
```

### Step 4 — Handle Review Actions

| Action | Effect |
|--------|--------|
| **Review all** | Show combined migration analysis for the entire cascade |
| **Approve cascade** | Approve all changes in the cascade as a single decision |
| **Review individually** | Break the cascade back into individual review items |
| **Defer cascade** | Defer all changes in the cascade together |

The human can always break a cascade into individual items if they want granular control. The cascade is a presentation convenience, not a constraint.

---

## Non-Cascading Changes

Changes that don't match any cascade pattern are presented as individual review items, exactly as they would be without cascade detection. Cascade detection is additive — it groups related items but never alters how non-cascading items are presented.

---

## Custom Cascades

The known cascade patterns above are built-in defaults. Projects can define additional cascade rules in `config.json` if they have project-specific tool relationships:

```json
{
  "cascade_rules": [
    {
      "trigger": "storybook",
      "related": ["chromatic", "addon-essentials"],
      "name": "Storybook Ecosystem"
    }
  ]
}
```

Custom rules follow the same detection and grouping logic as built-in patterns.
