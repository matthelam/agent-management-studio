"""
stack_detect — Step 2: detect runtime, frameworks, and toolchain.

Reads package.json / lock files (manifest-only sampling) and calls
Claude (Sonnet, structured output) to produce a StackSnapshotModel.
"""

from __future__ import annotations

from state import GraphState, add_error
from state import StackSnapshotModel
from call_claude import structured
from config import SONNET
from logger import step_start, step_end, artifact_write


def run(state: GraphState) -> GraphState:
    """
    - Sample manifest files from sweep (package.json, *.csproj, pyproject.toml, etc.)
    - Call structured(schema=StackSnapshotModel) with manifest content
    - Validate via Pydantic (SDK enforces schema)
    - Set state["stack"] = model.model_dump()
    """
    raise NotImplementedError("stack_detect not yet implemented")
