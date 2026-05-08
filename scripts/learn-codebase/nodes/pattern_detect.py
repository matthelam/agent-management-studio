"""
pattern_detect — Step 4a: multi-agent pattern scanning.

Three parallel sub-agents (systematist, specifist, pragmatist) each scan
the codebase from their distinct cognitive perspective. An Opus synthesizer
combines their reports into patterns.md.
"""

from __future__ import annotations

from state import GraphState, add_error
from call_claude import run_agents, freetext
from config import SONNET, OPUS, PATTERN_DETECT_AGENTS, PATTERN_SYNTHESIS_INSTRUCTION
from logger import step_start, step_end, pattern_detected, artifact_write


def run(state: GraphState) -> GraphState:
    """
    Requires: state["stack_gate_passed"] == True

    1. Build shared_context from sweep file sample (Option B: smart sample)
    2. run_agents(PATTERN_DETECT_AGENTS, shared_context) → 3 agent reports
    3. Prepend PATTERN_SYNTHESIS_INSTRUCTION, call freetext(model=OPUS) → patterns.md
    4. Set state["patterns_md"] = synthesized text
    5. Log pattern_detected events for any ESTABLISHED patterns found
    """
    raise NotImplementedError("pattern_detect not yet implemented")
