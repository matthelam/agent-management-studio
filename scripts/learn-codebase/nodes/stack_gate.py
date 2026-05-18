"""
stack_gate — Human gate after stack_detect + build_deploy.

Presents the detected stack snapshot and build/deploy commands to the
user for confirmation before pattern/approach scanning begins.
On resume the user's response is stored as corrections if non-empty.
"""

from __future__ import annotations

import json

from langgraph.types import interrupt

from state import GraphState, has_fatal_error
from logger import step_start, step_end, human_gate as log_human_gate


GATE_NAME = "stack_gate"


def _build_prompt(state: GraphState) -> str:
    stack = state.get("stack") or {}
    bd = state.get("build_deploy") or {}
    lines = [
        "-- STACK GATE --------------------------------------------",
        "Review the detected stack and build commands below.",
        "Type 'yes' to approve and continue, or describe any corrections.",
        "",
        "STACK:",
        json.dumps(stack, indent=2),
        "",
        "BUILD / DEPLOY:",
        json.dumps(bd, indent=2),
        "----------------------------------------------------------",
    ]
    return "\n".join(lines)


def run(state: GraphState) -> GraphState:
    if has_fatal_error(state):
        return state

    meta = state["meta"]
    log = meta["log_file"]

    step_start(log, "3b-stack_gate", GATE_NAME)
    prompt = _build_prompt(state)
    log_human_gate(log, GATE_NAME, "open", prompt_shown=prompt)

    response = interrupt({"gate": GATE_NAME, "prompt": prompt})

    log_human_gate(log, GATE_NAME, "closed", response=str(response))
    state["stack_gate_passed"] = True
    resp_str = str(response).strip()
    if resp_str.lower() not in ("yes", "y", "approved", "approve"):
        state["stack_gate_corrections"] = resp_str

    step_end(log, "3b-stack_gate", GATE_NAME, "passed")
    return state
