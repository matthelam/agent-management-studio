"""
guardrails_parse — Step 5: extract GUARD RAIL lines from approaches.md.

Uses the canonical regex parser (not LLM) to convert GUARD RAILS sections
in approaches.md into structured GuardRail objects stored in graph state.
"""

from __future__ import annotations

import hashlib
import re

from config import GUARDRAIL_ACTIONS
from state import GraphState, GuardRail, has_fatal_error, add_warning
from logger import step_start, step_end, prescriptive_rule_generated


# Canonical GUARD RAIL line format:
#   - <path-or-glob> — <READ ONLY|BLOCK|MODIFY WITH CAUTION> for agents
# Also accepts READ-ONLY (hyphenated) and trailing description text after action token.
_GUARDRAIL_RE = re.compile(
    r"^\s*-\s+(.+?)\s+[—–\-]\s+\*{0,2}(READ[\s\-]ONLY|BLOCK|MODIFY WITH CAUTION)\*{0,2}",
    re.IGNORECASE,
)

# Section detection: matches "## GUARD RAILS", "## 10. GUARD RAILS",
# "GUARD RAILS:", and plain "GUARD RAILS" (no markdown heading).
_SECTION_START_RE = re.compile(
    r"^(#+\s*)?(\d+\.\s+)?GUARD\s*RAILS?\s*:?\s*$", re.IGNORECASE
)


def _make_id(path_glob: str, action: str) -> str:
    return hashlib.sha256(f"{path_glob}:{action}".encode()).hexdigest()[:12]


def parse_guard_rails(approaches_md: str) -> tuple[list[GuardRail], list[str]]:
    """
    Extract all GUARD RAIL lines from approaches.md.
    Returns (rails, parse_warnings).
    """
    rails: list[GuardRail] = []
    warnings: list[str] = []
    in_guard_rails_section = False

    for line in approaches_md.splitlines():
        stripped = line.strip()

        if _SECTION_START_RE.match(stripped):
            in_guard_rails_section = True
            continue

        # Exit section on a new markdown heading (but not on plain-text approach labels)
        if in_guard_rails_section and re.match(r"^#+\s", stripped):
            in_guard_rails_section = False

        if not in_guard_rails_section:
            continue

        m = _GUARDRAIL_RE.match(line)
        if not m:
            # Ignore horizontal rules (--- / *** / ===) — not guard rail lines
            if stripped.startswith("-") and stripped and not re.match(r"^-{2,}$", stripped):
                warnings.append(f"Skipped malformed GUARD RAIL line: {stripped!r}")
            continue

        path_glob = m.group(1).strip().strip("`")
        # Normalise READ-ONLY → read only for table lookup
        action_token = m.group(2).strip().lower().replace("-", " ")

        if action_token not in GUARDRAIL_ACTIONS:
            warnings.append(f"Unknown action token '{action_token}' in: {stripped!r}")
            continue

        action, tools = GUARDRAIL_ACTIONS[action_token]
        rule_id = _make_id(path_glob, action)

        rails.append(GuardRail(
            id=rule_id,
            tools=tools,
            match={"path_glob": path_glob},
            action=action,
            reason="Extracted from approaches.md GUARD RAILS section",
        ))

    return rails, warnings


def run(state: GraphState) -> GraphState:
    if has_fatal_error(state):
        return state

    meta = state["meta"]
    log = meta["log_file"]

    if not state.get("approaches_md"):
        return state  # nothing to parse (stub mode produces empty string)

    step_start(log, "5-guardrails_parse", "guardrails_parse")

    rails, warnings = parse_guard_rails(state["approaches_md"])

    state["guard_rails"] = rails
    state["guard_rails_parse_warnings"] = warnings

    for r in rails:
        prescriptive_rule_generated(
            log, r["id"], r["match"]["path_glob"], r["action"], r["tools"]
        )

    for w in warnings:
        add_warning(state, w)

    step_end(log, "5-guardrails_parse", "guardrails_parse", "ok",
             f"{len(rails)} rails, {len(warnings)} warnings")
    return state
