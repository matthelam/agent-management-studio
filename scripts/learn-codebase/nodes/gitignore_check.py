"""
gitignore_check — Step 0.5: ensure .claude/logs/ is in .gitignore.
"""

from __future__ import annotations

from state import GraphState
from logger import step_start, step_end


def run(state: GraphState) -> GraphState:
    """
    - Read target .gitignore (create if absent)
    - Append '.claude/logs/' if not already present
    - Log artifact_write if modified
    """
    raise NotImplementedError("gitignore_check not yet implemented")
