"""
audit_log — Step 11: copy run log to target .claude/logs/.

Copies the JSONL run log from the AMS artifact directory to the
target repo's .claude/logs/ so it travels with the codebase.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from state import GraphState, has_fatal_error, add_warning
from logger import step_start, step_end, artifact_write as log_artifact_write


def run(state: GraphState) -> GraphState:
    if has_fatal_error(state):
        return state

    meta = state["meta"]
    log = meta["log_file"]
    target = Path(meta["target_path"])

    step_start(log, "11-audit_log", "audit_log")

    src = Path(log)
    if not src.exists():
        add_warning(state, f"audit_log: run log not found at {src}, skipping copy")
        step_end(log, "11-audit_log", "audit_log", "skipped", "log file missing")
        return state

    dest_dir = target / ".claude" / "logs"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{meta['run_id']}.jsonl"

    shutil.copy2(str(src), str(dest))
    log_artifact_write(log, f"logs/{meta['run_id']}.jsonl", str(dest))

    step_end(log, "11-audit_log", "audit_log", "ok")
    return state
