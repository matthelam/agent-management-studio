"""
tool_safety — Step 9: write prescriptive-rules.json from parsed guard rails.

Converts GuardRail objects from state into the prescriptive-rules.json
format used by Claude Code's tool permission system.
"""

from __future__ import annotations

import json
from pathlib import Path

from state import GraphState, add_error
from logger import step_start, step_end, artifact_write


def run(state: GraphState) -> GraphState:
    """
    Requires: state["guard_rails"] (may be empty list)

    1. Convert state["guard_rails"] to prescriptive-rules.json schema
    2. Write to <target_path>/.claude/prescriptive-rules.json
    3. Set state["tool_safety_written"] = True
    4. Log artifact_write
    """
    raise NotImplementedError("tool_safety not yet implemented")
