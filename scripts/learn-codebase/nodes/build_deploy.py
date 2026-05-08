"""
build_deploy — Step 3: detect canonical build, test, and deploy commands.

Reads package.json scripts, CI configs, and Makefiles and calls Claude
(Sonnet, structured output) to produce a BuildDeployModel.
"""

from __future__ import annotations

from pathlib import Path

from state import GraphState, has_fatal_error, add_error, BuildDeployModel
from call_claude import structured
from config import SONNET
from stub_helpers import is_stub, stub_build_deploy
from logger import step_start, step_end


_CI_GLOBS = [
    ".github/workflows/*.yml", ".github/workflows/*.yaml",
    "Makefile", "makefile", "GNUmakefile",
    "Dockerfile", "docker-compose*.yml", "docker-compose*.yaml",
    "*.buildspec.yml", "azure-pipelines.yml", "bitbucket-pipelines.yml",
    "vercel.json", "netlify.toml", "xmcloud.build.json",
]


def _sample_ci(files: list[str], target: Path) -> str:
    parts: list[str] = []
    for abs_path in files:
        p = Path(abs_path)
        rel = str(p.relative_to(target)) if p.is_relative_to(target) else p.name
        if any(p.match(g) for g in _CI_GLOBS) or p.name == "package.json":
            try:
                content = p.read_text(encoding="utf-8", errors="replace")
                if len(content) > 6000:
                    content = content[:6000] + "\n... (truncated)"
                parts.append(f"=== {rel} ===\n{content}")
            except OSError:
                pass
    return "\n\n".join(parts)


def run(state: GraphState) -> GraphState:
    if has_fatal_error(state):
        return state

    meta = state["meta"]
    log = meta["log_file"]

    step_start(log, "3-build_deploy", "build_deploy")

    if is_stub(state):
        state["build_deploy"] = stub_build_deploy()
        step_end(log, "3-build_deploy", "build_deploy", "ok", "stub")
        return state

    sweep = state.get("sweep")
    if not sweep:
        return add_error(state, "build_deploy", "sweep missing", fatal=True)

    target = Path(meta["target_path"])
    ci_content = _sample_ci(sweep["files_read"], target)

    system = (
        "You are a build-system analyst. Given project CI/CD and build files, "
        "identify the canonical build, test, and deploy commands along with any "
        "deployment prerequisites or known conflicts."
    )
    user = (
        f"Stack context: {state.get('stack', {}).get('solution_type', 'unknown')}\n\n"
        f"CI/CD and build files:\n\n{ci_content}"
    )

    try:
        model = structured(
            system_prompt=system,
            user_message=user,
            schema=BuildDeployModel,
            model=SONNET,
        )
        state["build_deploy"] = model.model_dump()
    except Exception as exc:
        return add_error(state, "build_deploy", str(exc), fatal=True)

    step_end(log, "3-build_deploy", "build_deploy", "ok")
    return state
