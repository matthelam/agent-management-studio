"""
seed — Step 10: verify claude-mem worker is reachable.

Observations are captured automatically by PostToolUse hooks during real
Claude Code sessions — there is no external write API. This step just
confirms the worker at port 37777 is running so the hooks we seeded into
the target's settings.json will have something to talk to on first open.

Non-fatal: if claude-mem is unavailable, a warning is logged and the run
continues. The seeded hooks will auto-start the worker on next session open.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from state import GraphState, has_fatal_error, add_warning
from logger import step_start, step_end


def _health_check(ams_home: str) -> bool:
    health_script = Path(ams_home) / "scripts" / "utils" / "claude-mem-health.py"
    if not health_script.exists():
        return False
    result = subprocess.run(
        [sys.executable, str(health_script), "--ensure"],
        capture_output=True, text=True,
    )
    return result.returncode == 0


def run(state: GraphState) -> GraphState:
    if has_fatal_error(state):
        return state

    meta = state["meta"]
    log = meta["log_file"]

    step_start(log, "10-seed", "seed")

    if not _health_check(meta["ams_home"]):
        add_warning(state, "seed: claude-mem worker not reachable — hooks seeded but "
                    "worker is not running. Start it with: npx claude-mem start")

    state["seed_complete"] = True
    step_end(log, "10-seed", "seed", "ok", "worker health checked")
    return state
