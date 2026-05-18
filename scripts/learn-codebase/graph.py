"""
graph.py — LangGraph DAG for the learn-codebase pipeline.

Node execution order:
  preflight → gitignore_check → file_sweep
  → stack_detect → build_deploy → stack_gate (interrupt)
  → pattern_detect → approach_detect → guardrails_extract
  → team_propose → team_gate (interrupt)
  → domain_skills → assemble_manifest → tool_safety
  → seed → audit_log → final_report

All nodes short-circuit on fatal errors; final_report always runs.
Human gates use langgraph.types.interrupt() — graph pauses and resumes
via Command(resume=<user_response>).
"""

from __future__ import annotations

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

from state import GraphState
from nodes import (
    preflight,
    gitignore_check,
    file_sweep,
    stack_detect,
    build_deploy,
    stack_gate,
    pattern_detect,
    approach_detect,
    guardrails_extract,
    team_propose,
    team_gate,
    domain_skills,
    assemble_manifest,
    tool_safety,
    seed,
    audit_log,
    final_report,
)

# Sequential node pipeline — order matters
# Node names must not collide with GraphState field names.
# build_deploy and domain_skills are both state fields, so we prefix them.
_PIPELINE: list[tuple[str, object]] = [
    ("preflight",              preflight),
    ("gitignore_check",        gitignore_check),
    ("file_sweep",             file_sweep),
    ("stack_detect",           stack_detect),
    ("detect_build_deploy",    build_deploy),    # avoids clash with state["build_deploy"]
    ("stack_gate",             stack_gate),
    ("pattern_detect",         pattern_detect),
    ("approach_detect",        approach_detect),
    ("guardrails_extract",     guardrails_extract),
    ("team_propose",           team_propose),
    ("team_gate",              team_gate),
    ("generate_domain_skills", domain_skills),   # avoids clash with state["domain_skills"]
    ("assemble_manifest",      assemble_manifest),
    ("tool_safety",            tool_safety),
    ("seed",                   seed),
    ("audit_log",              audit_log),
    ("final_report",           final_report),
]


def _build() -> StateGraph:
    builder = StateGraph(GraphState)

    for name, mod in _PIPELINE:
        builder.add_node(name, mod.run)

    builder.set_entry_point(_PIPELINE[0][0])

    for i in range(len(_PIPELINE) - 1):
        builder.add_edge(_PIPELINE[i][0], _PIPELINE[i + 1][0])

    builder.add_edge(_PIPELINE[-1][0], END)
    return builder


def make_graph(checkpoint_db: str):
    """Compile the graph with a SqliteSaver checkpointer.

    Uses a direct sqlite3 connection (not the context-manager form) so the
    checkpointer stays alive across the full process lifetime and persists
    state between fresh-run and resume invocations.
    """
    import sqlite3
    conn = sqlite3.connect(checkpoint_db, check_same_thread=False)
    memory = SqliteSaver(conn)
    builder = _build()
    return builder.compile(checkpointer=memory)
