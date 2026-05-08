"""
build_deploy — Step 3: detect canonical build, test, and deploy commands.

Reads package.json scripts, Makefiles, CI configs (manifest-only sampling)
and calls Claude (Sonnet, structured output) to produce BuildDeployModel.
"""

from __future__ import annotations

from state import GraphState, add_error
from state import BuildDeployModel
from call_claude import structured
from config import SONNET
from logger import step_start, step_end


def run(state: GraphState) -> GraphState:
    """
    - Sample CI/CD manifests: package.json scripts, .github/workflows/, Makefile, etc.
    - Call structured(schema=BuildDeployModel)
    - Set state["build_deploy"] = model.model_dump()
    """
    raise NotImplementedError("build_deploy not yet implemented")
