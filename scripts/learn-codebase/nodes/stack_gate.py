"""
stack_gate — Human gate after stack_detect and build_deploy.

Presents the detected stack snapshot and build/deploy commands to the
user for confirmation before pattern / approach scanning begins.
"""

from __future__ import annotations

from state import GraphState
from checkpoint_io import write_gate_checkpoint, gate_state_summary
from logger import human_gate as log_human_gate, checkpoint_write


GATE_NAME = "stack_gate"


def run(state: GraphState) -> GraphState:
    """
    - Serialise stack + build_deploy into a human-readable summary
    - Write gate checkpoint file
    - Log human_gate event (state=open)
    - Raise langgraph.errors.GraphInterrupt to pause the graph
    - On resume: set state["stack_gate_passed"] = True (or capture corrections)
    """
    raise NotImplementedError("stack_gate not yet implemented")
