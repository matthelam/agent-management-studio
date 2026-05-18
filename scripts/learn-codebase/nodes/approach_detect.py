"""
approach_detect — Step 4b: multi-agent architectural approach scanning.

Three sub-agents (architect, empiricist, pragmatist) analyse architectural
decisions. An Opus synthesizer produces approaches.md with classified
GUARD RAIL candidates.
"""

from __future__ import annotations

import json
from pathlib import Path

from state import GraphState, has_fatal_error, add_error
from call_claude import run_agents, freetext
from config import SONNET, OPUS, APPROACH_DETECT_AGENTS, APPROACH_SYNTHESIS_INSTRUCTION
from stub_helpers import is_stub, STUB_APPROACHES_MD
from logger import step_start, step_end
from sampling import smart_sample


def run(state: GraphState) -> GraphState:
    if has_fatal_error(state):
        return state

    meta = state["meta"]
    log = meta["log_file"]

    step_start(log, "4b-approach_detect", "approach_detect")

    if is_stub(state):
        state["approaches_md"] = STUB_APPROACHES_MD
        step_end(log, "4b-approach_detect", "approach_detect", "ok", "stub")
        return state

    sweep = state.get("sweep")
    if not sweep:
        return add_error(state, "approach_detect", "sweep missing", fatal=True)

    target = Path(meta["target_path"])

    source_sample = smart_sample(sweep["files_read"], target)

    stack_summary = json.dumps(state.get("stack") or {}, indent=2)
    patterns_summary = state.get("patterns_md") or "(no patterns detected)"
    shared_context = (
        f"STACK:\n{stack_summary}\n\n"
        f"PATTERNS (already detected):\n{patterns_summary}\n\n"
        f"---\n\n{source_sample}"
    )

    try:
        agent_results = run_agents(APPROACH_DETECT_AGENTS, shared_context, model=SONNET)
        combined = "\n\n---\n\n".join(
            f"### {r['harness'].upper()} REPORT\n\n{r['output']}"
            for r in agent_results
        )
        approaches_md = freetext(
            system_prompt=APPROACH_SYNTHESIS_INSTRUCTION,
            user_message=f"Three agent reports to synthesise:\n\n{combined}",
            model=OPUS,
        )
        state["approaches_md"] = approaches_md
    except Exception as exc:
        return add_error(state, "approach_detect", str(exc), fatal=True)

    step_end(log, "4b-approach_detect", "approach_detect", "ok")
    return state
