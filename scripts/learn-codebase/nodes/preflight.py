"""
preflight — Step 0: validate target directory, existing seed detection,
rebuild confirmation gate.
"""

from __future__ import annotations

from state import GraphState, add_error, add_warning
from logger import step_start, step_end, human_gate


def run(state: GraphState) -> GraphState:
    """
    - Verify target_path exists and is a git repo
    - Detect existing .claude/ seed
    - If seed found: set existing_seed_detected=True, pause for rebuild confirmation gate
    """
    raise NotImplementedError("preflight not yet implemented")
