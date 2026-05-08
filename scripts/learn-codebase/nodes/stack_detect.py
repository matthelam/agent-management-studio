"""
stack_detect — Step 2: detect runtime, frameworks, and toolchain.

Reads package.json / lock files (manifest-only sampling) and calls
Claude (Sonnet, structured output) to produce a StackSnapshotModel.
"""

from __future__ import annotations

from state import GraphState, has_fatal_error, add_error, StackSnapshotModel
from call_claude import structured
from config import SONNET
from stub_helpers import is_stub, stub_stack
from logger import step_start, step_end

import json
from pathlib import Path


_MANIFEST_GLOBS = [
    "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "*.csproj", "*.fsproj", "pyproject.toml", "requirements*.txt",
    "turbo.json", "nx.json", "pnpm-workspace.yaml",
]


def _sample_manifests(files: list[str], target: Path) -> str:
    """Read manifest files from the sweep and concatenate their content."""
    parts: list[str] = []
    for abs_path in files:
        p = Path(abs_path)
        rel = str(p.relative_to(target)) if p.is_relative_to(target) else p.name
        if any(p.match(g) for g in _MANIFEST_GLOBS):
            try:
                content = p.read_text(encoding="utf-8", errors="replace")
                # Truncate very large lock files
                if len(content) > 8000:
                    content = content[:8000] + "\n... (truncated)"
                parts.append(f"=== {rel} ===\n{content}")
            except OSError:
                pass
    return "\n\n".join(parts)


def run(state: GraphState) -> GraphState:
    if has_fatal_error(state):
        return state

    meta = state["meta"]
    log = meta["log_file"]

    step_start(log, "2-stack_detect", "stack_detect")

    if is_stub(state):
        state["stack"] = stub_stack()
        step_end(log, "2-stack_detect", "stack_detect", "ok", "stub")
        return state

    sweep = state.get("sweep")
    if not sweep:
        return add_error(state, "stack_detect", "sweep missing", fatal=True)

    target = Path(meta["target_path"])
    manifest_content = _sample_manifests(sweep["files_read"], target)

    if not manifest_content:
        return add_error(state, "stack_detect",
                         "no manifest files found in sweep", fatal=True)

    system = (
        "You are a software stack analyst. Given manifest files, produce an accurate "
        "structured snapshot of the project's runtime, package manager, frameworks, "
        "testing tools, linting config, and key dependencies."
    )
    user = f"Analyse these manifest files:\n\n{manifest_content}"

    try:
        model = structured(
            system_prompt=system,
            user_message=user,
            schema=StackSnapshotModel,
            model=SONNET,
        )
        state["stack"] = model.model_dump()
    except Exception as exc:
        return add_error(state, "stack_detect", str(exc), fatal=True)

    step_end(log, "2-stack_detect", "stack_detect", "ok")
    return state
