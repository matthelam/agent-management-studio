"""
approach_detect — Step 4b: multi-agent architectural approach scanning.

Three parallel sub-agents (architect, empiricist, pragmatist) analyse
architectural decisions and boundaries. An Opus synthesizer produces
approaches.md with GUARD RAIL candidates classified as CERTAIN/PROBABLE.
"""

from __future__ import annotations

from state import GraphState, add_error
from call_claude import run_agents, freetext
from config import SONNET, OPUS, APPROACH_DETECT_AGENTS, APPROACH_SYNTHESIS_INSTRUCTION
from logger import step_start, step_end, approach_detected, artifact_write


def run(state: GraphState) -> GraphState:
    """
    Requires: state["stack_gate_passed"] == True and state["patterns_md"] is not None

    1. Build shared_context combining sweep file sample + patterns.md
    2. run_agents(APPROACH_DETECT_AGENTS, shared_context) → 3 agent reports
    3. Prepend APPROACH_SYNTHESIS_INSTRUCTION, call freetext(model=OPUS) → approaches.md
    4. Set state["approaches_md"] = synthesized text
    5. Log approach_detected events for CERTAIN/PROBABLE candidates
    """
    raise NotImplementedError("approach_detect not yet implemented")
