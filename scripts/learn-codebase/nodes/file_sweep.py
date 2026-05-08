"""
file_sweep — Step 1: deterministic file inventory of the target repo.

Walks the target directory, respects .gitignore, records every file path.
Produces SweepResult stored in state["sweep"].
"""

from __future__ import annotations

from state import GraphState
from logger import step_start, step_end, artifact_write


def run(state: GraphState) -> GraphState:
    """
    - Walk target_path, honour .gitignore exclusions
    - Collect absolute paths into SweepResult.files_read
    - Set state["sweep"] with file_count and completed_at
    """
    raise NotImplementedError("file_sweep not yet implemented")
