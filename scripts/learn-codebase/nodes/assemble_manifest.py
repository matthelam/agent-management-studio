"""
assemble_manifest — Step 8: write config.json and compute content hashes.

Assembles the final config.json from all validated graph state,
computes sha256 hashes for patterns.md and approaches.md,
and writes both files to the target .claude/ directory.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from state import GraphState, add_error
from logger import step_start, step_end, artifact_write


def sha256_content(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run(state: GraphState) -> GraphState:
    """
    Requires: patterns_md, approaches_md, stack, build_deploy, cognitive_team, domain_skills

    1. Compute content_hashes for patterns_md and approaches_md
    2. Set state["content_hashes"] (no "pending-first-write" values allowed)
    3. Assemble config.json dict from all state components
    4. Write config.json to <target_path>/.claude/config.json
    5. Write patterns.md and approaches.md to <target_path>/.claude/
    6. Log artifact_write for each file
    """
    raise NotImplementedError("assemble_manifest not yet implemented")
