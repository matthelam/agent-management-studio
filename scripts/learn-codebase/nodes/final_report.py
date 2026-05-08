"""
final_report — Step 12: emit invocation_end event and print summary.

Terminal node. Always runs — even after fatal errors — so the user
always gets a clear outcome report.
"""

from __future__ import annotations

from state import GraphState, has_fatal_error
from logger import invocation_end, step_start, step_end


def run(state: GraphState) -> GraphState:
    meta = state["meta"]
    log = meta["log_file"]

    step_start(log, "12-final_report", "final_report")

    errors = state.get("errors", [])
    warnings = state.get("warnings", [])
    fatal = has_fatal_error(state)
    outcome = "fatal_error" if fatal else "success"

    invocation_end(
        log,
        run_id=meta["run_id"],
        outcome=outcome,
        observations_seeded=state.get("observations_seeded", 0),
        observation_failures=state.get("observation_failures", 0),
        errors=errors,
    )

    # ---- stdout summary (Claude Code presents this to the user) ----
    line = "=" * 62
    print(f"\n{line}")
    print(f"  learn-codebase  run_id={meta['run_id']}  {outcome.upper()}")
    print(line)
    print(f"  target : {meta['target_path']}")
    print(f"  log    : {log}")

    if state.get("sweep"):
        print(f"  files  : {state['sweep']['file_count']}")

    skills = state.get("domain_skills", [])
    if skills:
        print(f"  skills : {', '.join(ds['name'] for ds in skills)}")

    rails = state.get("guard_rails", [])
    if rails:
        print(f"  rails  : {len(rails)}")

    obs = state.get("observations_seeded", 0)
    if obs:
        print(f"  seeded : {obs} observations")

    if warnings:
        print(f"\n  WARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"    • {w}")

    if errors:
        print(f"\n  ERRORS ({len(errors)}):")
        for e in errors:
            tag = "[FATAL]" if e.get("fatal") else "[error]"
            print(f"    {tag} [{e['step']}] {e['message']}")

    print(line + "\n")

    step_end(log, "12-final_report", "final_report", outcome)
    return state
