"""
seed — Step 10: seed observations into claude-mem.

For each seedable artifact (patterns.md, approaches.md, config.json,
domain skill files) calls claude-mem add-observation to persist the
content as searchable memory entries.
"""

from __future__ import annotations

from state import GraphState, add_error, add_warning
from logger import step_start, step_end


def run(state: GraphState) -> GraphState:
    """
    Requires: state["seed_complete"] precondition artifacts all written

    1. For each artifact: run subprocess claude-mem add-observation
    2. Increment state["observations_seeded"] on success
    3. Increment state["observation_failures"] on failure (non-fatal)
    4. Set state["seed_complete"] = True when all attempted
    """
    raise NotImplementedError("seed not yet implemented")
