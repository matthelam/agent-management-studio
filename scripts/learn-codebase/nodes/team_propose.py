"""
team_propose — Step 6: propose the cognitive team configuration.

Calls Claude (Sonnet, structured output) with the detected stack and
patterns to produce a CognitiveTeamProposal.
"""

from __future__ import annotations

from state import GraphState, add_error
from state import CognitiveTeamProposal
from call_claude import structured
from config import SONNET
from logger import step_start, step_end


def run(state: GraphState) -> GraphState:
    """
    Requires: state["patterns_md"] and state["stack"] are populated

    1. Build prompt from stack snapshot + patterns summary
    2. Call structured(schema=CognitiveTeamProposal)
    3. Set state["cognitive_team"] = model.model_dump()
    """
    raise NotImplementedError("team_propose not yet implemented")
