"""
audit_log — Step 11: copy run log to target .claude/logs/.

Copies the JSONL run log from the AMS artifact directory to the
target repo's .claude/logs/ so it travels with the codebase.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from state import GraphState, add_warning
from logger import step_start, step_end, artifact_write


def run(state: GraphState) -> GraphState:
    """
    1. Source: state["meta"]["log_file"]  (AMS artifact dir)
    2. Dest:   <target_path>/.claude/logs/<run_id>.jsonl
    3. Create dest dir if needed
    4. Copy file, log artifact_write
    """
    raise NotImplementedError("audit_log not yet implemented")
