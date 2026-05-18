"""
team_propose — Step 6: propose the cognitive team configuration.

Calls Claude (Sonnet, structured output) with the detected stack and
patterns summary to produce a CognitiveTeamProposal.
"""

from __future__ import annotations

import json

from state import GraphState, has_fatal_error, add_error, CognitiveTeamProposal
from call_claude import structured
from config import SONNET, VALID_HARNESSES, VALID_LENSES
from stub_helpers import is_stub, stub_cognitive_team
from logger import step_start, step_end


def run(state: GraphState) -> GraphState:
    if has_fatal_error(state):
        return state

    meta = state["meta"]
    log = meta["log_file"]

    step_start(log, "6-team_propose", "team_propose")

    if is_stub(state):
        state["cognitive_team"] = stub_cognitive_team(meta["target_basename"])
        step_end(log, "6-team_propose", "team_propose", "ok", "stub")
        return state

    stack = json.dumps(state.get("stack") or {}, indent=2)
    patterns_excerpt = (state.get("patterns_md") or "")[:3000]

    system = (
        f"You are configuring a cognitive agent team for a software project.\n"
        f"Available harnesses: {', '.join(sorted(VALID_HARNESSES))}\n"
        f"Available lenses: {', '.join(sorted(VALID_LENSES))}\n\n"
        "Select the most appropriate team for this project's needs. "
        "The work_item_prefix must be 2-3 uppercase letters derived from the project name."
    )
    user = (
        f"Project: {meta['target_basename']}\n\n"
        f"Stack:\n{stack}\n\n"
        f"Patterns (excerpt):\n{patterns_excerpt}"
    )

    try:
        model = structured(
            system_prompt=system,
            user_message=user,
            schema=CognitiveTeamProposal,
            model=SONNET,
        )
        state["cognitive_team"] = model.model_dump()
    except Exception as exc:
        return add_error(state, "team_propose", str(exc), fatal=True)

    step_end(log, "6-team_propose", "team_propose", "ok")
    return state
