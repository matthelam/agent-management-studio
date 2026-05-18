"""
preflight — Step 0: validate target directory, existing seed detection,
rebuild confirmation gate.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from langgraph.types import interrupt

from state import GraphState, add_error, add_warning
from logger import step_start, step_end, human_gate as log_human_gate


def run(state: GraphState) -> GraphState:
    meta = state["meta"]
    target = Path(meta["target_path"])
    log = meta["log_file"]

    step_start(log, "0-preflight", "preflight")

    if not target.exists() or not target.is_dir():
        step_end(log, "0-preflight", "preflight", "fatal",
                 f"target_path does not exist or is not a directory: {target}")
        return add_error(state, "preflight",
                         f"target_path does not exist or is not a directory: {target}")

    # Git repo check
    result = subprocess.run(
        ["git", "rev-parse", "--git-dir"],
        cwd=str(target), capture_output=True, text=True
    )
    if result.returncode != 0:
        step_end(log, "0-preflight", "preflight", "fatal", "not a git repository")
        return add_error(state, "preflight",
                         f"target_path is not a git repository: {target}")

    # Existing seed detection
    config_json = target / ".claude" / "config.json"
    if config_json.exists():
        state["existing_seed_detected"] = True
        prompt = (
            f"An existing .claude/ seed was found in:\n  {target}\n\n"
            "Rebuild from scratch? This will overwrite all existing .claude/ artifacts.\n"
            "Type 'yes' to rebuild or anything else to abort."
        )
        log_human_gate(log, "rebuild_confirmation", "open", prompt_shown=prompt)
        response = interrupt({"gate": "rebuild_confirmation", "prompt": prompt})
        log_human_gate(log, "rebuild_confirmation", "closed", response=str(response))

        if str(response).strip().lower() not in ("yes", "y"):
            step_end(log, "0-preflight", "preflight", "aborted", "rebuild declined")
            return add_error(state, "preflight", "Rebuild declined by user.")

        state["rebuild_confirmed"] = True

    step_end(log, "0-preflight", "preflight", "ok")
    return state
