"""
seed — Step 10: seed observations into claude-mem.

Calls claude-mem-health to check readiness, then seeds key artifacts.
Non-fatal: if claude-mem is unavailable, logs a warning and continues.
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
        capture_output=True, text=True
    )
    return result.returncode == 0


def _seed_observation(content: str, tags: list[str]) -> bool:
    """Attempt to add a single observation to claude-mem. Returns True on success."""
    try:
        result = subprocess.run(
            ["npx", "claude-mem", "add-observation",
             "--content", content,
             "--tags", ",".join(tags)],
            capture_output=True, text=True, timeout=30
        )
        return result.returncode == 0
    except Exception:
        return False


def run(state: GraphState) -> GraphState:
    if has_fatal_error(state):
        return state

    meta = state["meta"]
    log = meta["log_file"]

    step_start(log, "10-seed", "seed")

    if not _health_check(meta["ams_home"]):
        add_warning(state, "seed: claude-mem not healthy — skipping observation seeding")
        state["seed_complete"] = True
        step_end(log, "10-seed", "seed", "skipped", "claude-mem unavailable")
        return state

    artifacts = [
        {
            "content": f"Stack snapshot for {meta['target_basename']}: "
                       f"{state.get('stack', {})}",
            "tags": ["stack", meta["target_basename"]],
        },
        {
            "content": f"Build/deploy commands for {meta['target_basename']}: "
                       f"{state.get('build_deploy', {})}",
            "tags": ["build-deploy", meta["target_basename"]],
        },
    ]

    # Seed patterns.md summary (first 1000 chars)
    if state.get("patterns_md"):
        artifacts.append({
            "content": f"Code patterns for {meta['target_basename']}:\n"
                       + (state["patterns_md"] or "")[:1000],
            "tags": ["patterns", meta["target_basename"]],
        })

    seeded = 0
    failures = 0
    for art in artifacts:
        if _seed_observation(art["content"], art["tags"]):
            seeded += 1
        else:
            failures += 1

    state["observations_seeded"] = seeded
    state["observation_failures"] = failures
    state["seed_complete"] = True

    if failures:
        add_warning(state, f"seed: {failures} observation(s) failed to seed")

    step_end(log, "10-seed", "seed", "ok", f"{seeded} seeded, {failures} failed")
    return state
