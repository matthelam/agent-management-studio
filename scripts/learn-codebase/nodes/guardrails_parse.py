"""
guardrails_parse — Step 5: extract GUARD RAIL lines from approaches.md.

Uses the canonical regex parser (not LLM) to convert GUARD RAILS sections
in approaches.md into structured GuardRail objects stored in graph state.
"""

from __future__ import annotations

import hashlib
import re
from typing import Optional

from config import GUARDRAIL_ACTIONS
from state import GraphState, GuardRail, add_warning
from logger import step_start, step_end, prescriptive_rule_generated


# Canonical GUARD RAIL line format:
#   - <path-or-glob> — <READ ONLY|BLOCK|MODIFY WITH CAUTION> for agents
_GUARDRAIL_RE = re.compile(
    r"^\s*-\s+(.+?)\s+[—–-]\s+(READ ONLY|BLOCK|MODIFY WITH CAUTION)\s+for\s+agents",
    re.IGNORECASE,
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

        if re.match(r"^#+\s*GUARD\s*RAILS?", stripped, re.IGNORECASE):
            in_guard_rails_section = True
            continue

        if in_guard_rails_section and re.match(r"^#+\s", stripped):
            in_guard_rails_section = False

        if not in_guard_rails_section:
            continue

        m = _GUARDRAIL_RE.match(line)
        if not m:
            if stripped.startswith("-") and stripped:
                warnings.append(f"Skipped malformed GUARD RAIL line: {stripped!r}")
            continue

        path_glob = m.group(1).strip()
        action_token = m.group(2).strip().lower()

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
            reason=f"Extracted from approaches.md GUARD RAILS section",
        ))

    return rails, warnings


def run(state: GraphState) -> GraphState:
    """
    Requires: state["approaches_md"] is not None

    1. Call parse_guard_rails(state["approaches_md"])
    2. Set state["guard_rails"] and state["guard_rails_parse_warnings"]
    3. Log a prescriptive_rule_generated event per rail
    """
    raise NotImplementedError("guardrails_parse.run() not yet implemented — parser logic above is ready")
