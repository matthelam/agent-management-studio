"""
tool_safety — Step 9: write prescriptive-rules.json from parsed guard rails.

Converts GuardRail objects from state into the prescriptive-rules.json
format used by Claude Code's tool permission system.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from state import GraphState, has_fatal_error
from logger import step_start, step_end, artifact_write as log_artifact_write


def run(state: GraphState) -> GraphState:
    if has_fatal_error(state):
        return state

    meta = state["meta"]
    target = Path(meta["target_path"])
    log = meta["log_file"]
    claude_dir = target / ".claude"
    claude_dir.mkdir(exist_ok=True)

    step_start(log, "9-tool_safety", "tool_safety")

    rules_payload = {
        "schema_version": 1,
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "run_id": meta["run_id"],
        "rules": list(state.get("guard_rails", [])),
    }

    rules_path = claude_dir / "prescriptive-rules.json"
    rules_path.write_text(
        json.dumps(rules_payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    log_artifact_write(log, "prescriptive-rules.json", str(rules_path))

    state["tool_safety_written"] = True
    step_end(log, "9-tool_safety", "tool_safety", "ok",
             f"{len(state.get('guard_rails', []))} rules written")
    return state
