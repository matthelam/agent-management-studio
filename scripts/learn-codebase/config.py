"""
Centralised constants for the learn-codebase graph.

Model IDs, harness names, canonical skill umbrella table,
valid enums — all in one place so nodes never hardcode strings.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Model IDs
# ---------------------------------------------------------------------------

SONNET = "claude-sonnet-4-6"   # structured nodes + sub-agents
OPUS   = "claude-opus-4-7"     # synthesis nodes (pattern + approach orchestrators)

# ---------------------------------------------------------------------------
# Cognitive harness names
# ---------------------------------------------------------------------------

VALID_HARNESSES: frozenset[str] = frozenset({
    "empiricist",
    "specifist",
    "synthesizer",
    "architect",
    "skeptic",
    "pragmatist",
    "systematist",
})

VALID_LENSES: frozenset[str] = frozenset({
    "accessibility",
    "security",
    "performance",
    "ux",
    "devils-advocate",
})

# ---------------------------------------------------------------------------
# Domain skill umbrella table
# Detection signals → canonical skill name (order = priority)
# ---------------------------------------------------------------------------

UMBRELLA_TABLE: list[tuple[frozenset[str], str]] = [
    (
        frozenset([
            "@sitecore-content-sdk", "@sitecore-feaas", "@sitecore-jss",
            "sitecore.json", ".scproj", "sitecore-content-serialization",
            "@sitecore-cloudsdk", "@sitecore-search",
        ]),
        "sitecore-knowledge",
    ),
    (
        frozenset(["next", "@next/"]),
        "nextjs-knowledge",
    ),
    (
        frozenset([
            "tailwindcss", "@radix-ui", "class-variance-authority",
            "@shadcn", "shadcn",
        ]),
        "tailwind-radix-knowledge",
    ),
    (
        frozenset(["@mantine"]),
        "mantine-knowledge",
    ),
    (
        frozenset(["turbo", "turbo.json", "nx.json", "pnpm-workspace"]),
        "monorepo-turbo-knowledge",
    ),
    (
        frozenset(["@storybook", "storybook"]),
        "storybook-knowledge",
    ),
    (
        frozenset(["docker", "dockerfile", "docker-compose"]),
        "docker-knowledge",
    ),
]

MAX_DOMAIN_SKILLS = 10

# ---------------------------------------------------------------------------
# Altitude bands
# ---------------------------------------------------------------------------

VALID_ALTITUDE_BANDS: frozenset[str] = frozenset({
    "maker", "planner", "navigator",
})

# ---------------------------------------------------------------------------
# Solution types
# ---------------------------------------------------------------------------

VALID_SOLUTION_TYPES: frozenset[str] = frozenset({
    "headless-nextjs",
    "headless-monorepo-turbo",
    "dotnet-app",
    "sitecore-xmc",
    "sitecore-jss",
    "hybrid-sitecore-content-sdk",
    "other",
})

# ---------------------------------------------------------------------------
# GUARD RAIL action tokens
# ---------------------------------------------------------------------------

GUARDRAIL_ACTIONS: dict[str, tuple[str, list[str]]] = {
    "read only":           ("block", ["Edit", "Write", "MultiEdit"]),
    "block":               ("block", ["Edit", "Write", "Bash", "MultiEdit"]),
    "modify with caution": ("warn",  ["Edit", "Write", "MultiEdit"]),
}

# ---------------------------------------------------------------------------
# Scan node harness assignments
# ---------------------------------------------------------------------------

PATTERN_DETECT_AGENTS = [
    ("systematist", "Scan every pattern category. Be comprehensive — breadth first. "
                    "Your goal is full coverage of all pattern types. "
                    "Do not miss a category."),
    ("specifist",   "Go deep on each pattern you find. Capture the exact signature, "
                    "evidence files with line numbers, edge cases, and what breaks the pattern."),
    ("pragmatist",  "Find only patterns that someone explicitly stated. "
                    "Scan documentation, README files, build scripts, and directive comments "
                    "(// DO NOT, // MUST, // IMPORTANT, AUTO-GENERATED etc). "
                    "Do not infer from code behaviour. Only report what was written down."),
]

APPROACH_DETECT_AGENTS = [
    ("architect",   "Map the architectural boundaries. Cross-package seams, deployment "
                    "boundaries, data flow decisions, integration points. What structural "
                    "choices constrain everything else?"),
    ("empiricist",  "Evidence-check every architectural claim. How many files confirm "
                    "each approach? What are the exceptions? Show counts and file paths. "
                    "Flag anything inconsistent with the stated architecture."),
    ("pragmatist",  "Find only architectural decisions that were explicitly documented. "
                    "Architecture docs, READMEs, build scripts, CI/CD structure, "
                    "warning comments. Especially look for 'never', 'always', 'do not', "
                    "caution statements — these are GUARD RAIL candidates."),
]

PATTERN_SYNTHESIS_INSTRUCTION = """\
You have three analysis reports. Cross-reference them before writing anything.

CONFIDENCE CLASSIFICATION:
- ESTABLISHED  — appears in code analysis (systematist + specifist) AND documented (pragmatist)
- INFERRED     — code analysis only. Not documented. Worth noting.
- DOCUMENTED   — pragmatist found it, code analysis does not confirm it.
                 Surface as: "stated intention — verify in code."
- CONFLICT     — code does X, documentation says Y. Surface as WARNING.

For each pattern you include:
- Use the specifist's formulation for precision
- Use the systematist's list to ensure no category is missed
- Mark CONFLICTS explicitly — these are the most actionable findings

Filter ruthlessly. Include a pattern only if it meets ALL:
  1. Appears in ≥3 files OR is architecturally significant (1-2 files but load-bearing)
  2. Has a derivable positive/negative example
  3. Would change how a developer writes new code if they knew about it

You have more context than belongs in the output. Prune, don't concatenate.\
"""

APPROACH_SYNTHESIS_INSTRUCTION = """\
You have three analysis reports. Cross-reference before writing anything.

GUARD RAIL CANDIDATE CLASSIFICATION:
- CERTAIN    — architect + empiricist confirm the boundary AND pragmatist found
               explicit documentation. Write the full GUARD RAIL.
- PROBABLE   — two of three agree. Write the approach, flag for human review.
- INFERRED   — code analysis only, nothing documented. Document the approach
               but do NOT generate a GUARD RAIL line.
- DOCUMENTED — pragmatist found it, code doesn't confirm. Surface as WARNING:
               "stated but not evidenced in code."

GUARD RAIL lines MUST follow this exact format (Step 8 parser depends on it):
  - <path-or-glob> — <READ ONLY|BLOCK|MODIFY WITH CAUTION> for agents

Only CERTAIN and PROBABLE candidates get a GUARD RAILS section.
INFERRED approaches are documented without a GUARD RAIL line.
You have more context than belongs in the output. Be selective.\
"""
