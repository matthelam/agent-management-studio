"""
gitignore_check — Step 0.5: ensure .claude/ is excluded from git tracking.

Uses .git/info/exclude (per-clone, never committed) so there is zero
AI footprint in the tracked repository. This aligns with the README's
"zero AI footprint in the cloud git repo" principle.
"""

from __future__ import annotations

from pathlib import Path

from state import GraphState, has_fatal_error
from logger import step_start, step_end, artifact_write as log_artifact_write


_EXCLUDE_ENTRY = ".claude/"


def run(state: GraphState) -> GraphState:
    if has_fatal_error(state):
        return state

    meta = state["meta"]
    target = Path(meta["target_path"])
    log = meta["log_file"]

    step_start(log, "0.5-gitignore_check", "gitignore_check")

    exclude_file = target / ".git" / "info" / "exclude"

    # .git/info/ always exists in a valid git repo
    if not exclude_file.parent.exists():
        exclude_file.parent.mkdir(parents=True, exist_ok=True)

    if exclude_file.exists():
        content = exclude_file.read_text(encoding="utf-8")
    else:
        content = ""

    if _EXCLUDE_ENTRY not in content.splitlines():
        with open(exclude_file, "a", encoding="utf-8") as fh:
            if content and not content.endswith("\n"):
                fh.write("\n")
            fh.write(f"{_EXCLUDE_ENTRY}\n")
        log_artifact_write(log, ".git/info/exclude", str(exclude_file))

    step_end(log, "0.5-gitignore_check", "gitignore_check", "ok")
    return state
