"""
team_gate — Human gate after team_propose.

Presents the proposed cognitive team to the user for confirmation
before domain skill generation and seeding.
"""

from __future__ import annotations

from state import GraphState
from checkpoint_io import write_gate_checkpoint, gate_state_summary
from logger import human_gate as log_human_gate, checkpoint_write


GATE_NAME = "team_gate"


def run(state: GraphState) -> GraphState:
    """
    - Serialise cognitive_team proposal into a human-readable summary
    - Write gate checkpoint file
    - Raise langgraph.errors.GraphInterrupt to pause the graph
    - On resume: set state["team_gate_passed"] = True (or capture corrections)
    """
    raise NotImplementedError("team_gate not yet implemented")
