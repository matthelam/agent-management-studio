"""
team_gate — Human gate after team_propose.

Presents the proposed cognitive team to the user for confirmation
before domain skill generation and seeding.
"""

from __future__ import annotations

import json

from langgraph.types import interrupt

from state import GraphState, has_fatal_error
from logger import step_start, step_end, human_gate as log_human_gate


GATE_NAME = "team_gate"


def _build_prompt(state: GraphState) -> str:
    team = state.get("cognitive_team") or {}
    lines = [
        "-- TEAM GATE ---------------------------------------------",
        "Review the proposed cognitive team configuration below.",
        "Type 'yes' to approve and continue, or describe any corrections.",
        "",
        "COGNITIVE TEAM:",
        json.dumps(team, indent=2),
        "----------------------------------------------------------",
    ]
    return "\n".join(lines)


def run(state: GraphState) -> GraphState:
    if has_fatal_error(state):
        return state

    meta = state["meta"]
    log = meta["log_file"]

    step_start(log, "6b-team_gate", GATE_NAME)
    prompt = _build_prompt(state)
    log_human_gate(log, GATE_NAME, "open", prompt_shown=prompt)

    response = interrupt({"gate": GATE_NAME, "prompt": prompt})

    log_human_gate(log, GATE_NAME, "closed", response=str(response))
    state["team_gate_passed"] = True
    resp_str = str(response).strip()
    if resp_str.lower() not in ("yes", "y", "approved", "approve"):
        state["team_gate_corrections"] = resp_str

    step_end(log, "6b-team_gate", GATE_NAME, "passed")
    return state
