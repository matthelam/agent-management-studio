"""
final_report — Step 12: emit invocation_end event and print summary.

Terminal node. Summarises what was seeded, any warnings, and
prints the graph run report to stdout for Claude Code to present.
"""

from __future__ import annotations

from state import GraphState
from logger import invocation_end, step_start, step_end


def run(state: GraphState) -> GraphState:
    """
    1. Log invocation_end event with outcome, counts, errors
    2. Print human-readable summary to stdout
    3. Return state unchanged (terminal node)
    """
    raise NotImplementedError("final_report not yet implemented")
