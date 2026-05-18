"""
file_sweep — Step 1: deterministic file inventory of the target repo.

Uses 'git ls-files --cached --others --exclude-standard' to enumerate
all files that git tracks or would track, excluding .gitignore'd paths.
Produces SweepResult stored in state["sweep"].
"""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path

from state import GraphState, SweepResult, has_fatal_error, add_error
from logger import step_start, step_end


def run(state: GraphState) -> GraphState:
    if has_fatal_error(state):
        return state

    meta = state["meta"]
    target = Path(meta["target_path"])
    log = meta["log_file"]

    step_start(log, "1-file_sweep", "file_sweep")

    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=str(target), capture_output=True, text=True
    )

    if result.returncode != 0:
        step_end(log, "1-file_sweep", "file_sweep", "fatal", result.stderr)
        return add_error(state, "file_sweep",
                         f"git ls-files failed: {result.stderr.strip()}")

    rel_paths = [p for p in result.stdout.splitlines() if p.strip()]
    abs_paths = [str(target / p) for p in rel_paths]

    state["sweep"] = SweepResult(
        files_read=abs_paths,
        file_count=len(abs_paths),
        completed_at=datetime.now(tz=timezone.utc).isoformat(),
    )

    step_end(log, "1-file_sweep", "file_sweep", "ok", f"{len(abs_paths)} files")
    return state
