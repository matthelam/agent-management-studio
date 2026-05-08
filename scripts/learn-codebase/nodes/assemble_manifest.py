"""
assemble_manifest — Step 8: write config.json and compute content hashes.

Assembles the final config.json from all validated graph state,
computes sha256 hashes for patterns.md and approaches.md,
and writes all three files to the target .claude/ directory.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from state import GraphState, has_fatal_error, add_error
from logger import step_start, step_end, artifact_write as log_artifact_write


def sha256_content(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run(state: GraphState) -> GraphState:
    if has_fatal_error(state):
        return state

    meta = state["meta"]
    target = Path(meta["target_path"])
    log = meta["log_file"]
    claude_dir = target / ".claude"
    claude_dir.mkdir(exist_ok=True)

    step_start(log, "8-assemble_manifest", "assemble_manifest")

    patterns_md = state.get("patterns_md") or ""
    approaches_md = state.get("approaches_md") or ""

    # Compute content hashes — no "pending-first-write" allowed
    hashes = {
        "patterns_md": sha256_content(patterns_md),
        "approaches_md": sha256_content(approaches_md),
    }
    state["content_hashes"] = hashes

    # Write patterns.md
    patterns_path = claude_dir / "patterns.md"
    patterns_path.write_text(patterns_md, encoding="utf-8")
    log_artifact_write(log, "patterns.md", str(patterns_path),
                       size_bytes=len(patterns_md.encode("utf-8")))

    # Write approaches.md
    approaches_path = claude_dir / "approaches.md"
    approaches_path.write_text(approaches_md, encoding="utf-8")
    log_artifact_write(log, "approaches.md", str(approaches_path),
                       size_bytes=len(approaches_md.encode("utf-8")))

    # Assemble config.json
    config = {
        "schema_version": 1,
        "run_id": meta["run_id"],
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "target": meta["target_path"],
        "target_basename": meta["target_basename"],
        "stack": state.get("stack"),
        "build_deploy": state.get("build_deploy"),
        "cognitive_team": state.get("cognitive_team"),
        "domain_skills": [
            {"name": ds["name"], "file_path": ds["file_path"]}
            for ds in state.get("domain_skills", [])
        ],
        "guard_rails_count": len(state.get("guard_rails", [])),
        "content_hashes": hashes,
    }

    config_path = claude_dir / "config.json"
    config_path.write_text(
        json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    log_artifact_write(log, "config.json", str(config_path))

    state["config_json_written"] = True
    step_end(log, "8-assemble_manifest", "assemble_manifest", "ok")
    return state
