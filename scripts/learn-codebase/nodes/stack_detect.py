"""
stack_detect — Step 2: detect runtime, frameworks, and toolchain.

Pre-extracts deterministic facts from manifest files first (node version,
package manager, framework versions, structural file presence). These facts
are passed as confirmed context to the LLM so it only synthesises the parts
Python cannot determine, and are stored in state for downstream verification.

After the LLM call, the verifier checks the output against the pre-extracted
facts. Blocking failures trigger one retry with the correction brief.
"""

from __future__ import annotations

import json
from pathlib import Path

from state import GraphState, has_fatal_error, add_error, add_warning, StackSnapshotModel
from call_claude import structured
from deterministic_facts import extract as extract_facts, DeterministicFacts
from verifier import verify, Assertion
from config import SONNET
from stub_helpers import is_stub, stub_stack
from logger import step_start, step_end, verification_result as log_vr


_MANIFEST_GLOBS = [
    "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "*.csproj", "*.fsproj", "pyproject.toml", "requirements*.txt",
    "turbo.json", "nx.json", "pnpm-workspace.yaml",
]


def _sample_manifests(files: list[str], target: Path) -> str:
    parts: list[str] = []
    for abs_path in files:
        p = Path(abs_path)
        rel = str(p.relative_to(target)) if p.is_relative_to(target) else p.name
        if any(p.match(g) for g in _MANIFEST_GLOBS):
            try:
                content = p.read_text(encoding="utf-8", errors="replace")
                if len(content) > 8000:
                    content = content[:8000] + "\n... (truncated)"
                parts.append(f"=== {rel} ===\n{content}")
            except OSError:
                pass
    return "\n\n".join(parts)


def _build_assertions(det: DeterministicFacts, model: StackSnapshotModel) -> list[Assertion]:
    return [
        Assertion(
            id="SD-001",
            description="Runtime node version matches package.json engines.node when specified",
            evidence=f"package.json engines.node: {det.node_version or 'not specified in any manifest'}",
            claim=f"LLM detected runtime.node: {model.runtime.get('node', 'not set')}",
            severity="warning",
        ),
        Assertion(
            id="SD-002",
            description="Package manager name matches the lockfile type present in the project",
            evidence=(
                f"Lockfile found: {det.pm_lockfile or 'none detected'} "
                f"(pnpm-lock.yaml→pnpm, yarn.lock→yarn, package-lock.json→npm)"
            ),
            claim=f"LLM detected package_manager.name: {model.package_manager.get('name', 'unknown')}",
            severity="blocking",
        ),
        Assertion(
            id="SD-003",
            description="Detected framework versions are consistent with package.json dependencies",
            evidence=f"package.json dependency versions: {json.dumps(det.framework_versions)}",
            claim=f"LLM detected frameworks: {json.dumps(model.frameworks)}",
            severity="warning",
        ),
        Assertion(
            id="SD-004",
            description="Project structure type is consistent with monorepo/workspace files found",
            evidence=(
                f"turbo.json: {det.has_turbo_json}, "
                f"pnpm-workspace.yaml: {det.has_pnpm_workspace}, "
                f"nx.json: {det.has_nx_json}"
            ),
            claim=(
                f"LLM detected structure.type: {model.structure.get('type', 'unknown')}, "
                f"orchestrator: {model.structure.get('orchestrator', 'none')}"
            ),
            severity="warning",
        ),
    ]


def _llm_call(system: str, user: str) -> StackSnapshotModel:
    return structured(
        system_prompt=system,
        user_message=user,
        schema=StackSnapshotModel,
        model=SONNET,
    )


def run(state: GraphState) -> GraphState:
    if has_fatal_error(state):
        return state

    meta = state["meta"]
    log  = meta["log_file"]

    step_start(log, "2-stack_detect", "stack_detect")

    if is_stub(state):
        state["stack"] = stub_stack()
        step_end(log, "2-stack_detect", "stack_detect", "ok", "stub")
        return state

    sweep = state.get("sweep")
    if not sweep:
        return add_error(state, "stack_detect", "sweep missing", fatal=True)

    target = Path(meta["target_path"])

    # --- Deterministic pre-extraction ---
    det = extract_facts(sweep["files_read"], target)
    state["det_facts"] = det.as_dict()

    manifest_content = _sample_manifests(sweep["files_read"], target)
    if not manifest_content:
        return add_error(state, "stack_detect",
                         "no manifest files found in sweep", fatal=True)

    confirmed = (
        f"Confirmed facts extracted directly from files (do not contradict these):\n"
        f"  node_version: {det.node_version or 'not specified'}\n"
        f"  package_manager: {det.package_manager or 'unknown'} "
        f"(lockfile: {det.pm_lockfile or 'none'})\n"
        f"  has_turbo_json: {det.has_turbo_json}\n"
        f"  has_pnpm_workspace: {det.has_pnpm_workspace}\n"
        f"  has_nx_json: {det.has_nx_json}\n"
        f"  has_sitecore_json: {det.has_sitecore_json}\n"
        f"  inferred_solution_type: {det.inferred_solution_type or 'ambiguous — use your judgement'}\n"
        f"  framework_versions: {json.dumps(det.framework_versions)}\n"
    )

    system = (
        "You are a software stack analyst. Given manifest files, produce an accurate "
        "structured snapshot of the project's runtime, package manager, frameworks, "
        "testing tools, linting config, and key dependencies."
    )
    user = f"{confirmed}\n\nAnalyse these manifest files:\n\n{manifest_content}"

    try:
        model = _llm_call(system, user)
    except Exception as exc:
        return add_error(state, "stack_detect", str(exc), fatal=True)

    # --- Verify ---
    assertions = _build_assertions(det, model)
    vr = verify("stack_detect", assertions)
    state["verification_results"]["stack_detect"] = vr.as_dict()
    log_vr(log, "stack_detect", vr.verdict,
           vr.failed_blocking, vr.failed_warnings, vr.correction_brief)

    # --- Retry on blocking failure ---
    if vr.has_blocking_failures():
        retry_user = (
            f"{user}\n\n"
            f"[VERIFICATION FAILED] Correction required:\n{vr.correction_brief}"
        )
        try:
            model = _llm_call(system, retry_user)
            vr2 = verify("stack_detect_retry", _build_assertions(det, model))
            state["verification_results"]["stack_detect_retry"] = vr2.as_dict()
            log_vr(log, "stack_detect_retry", vr2.verdict,
                   vr2.failed_blocking, vr2.failed_warnings, vr2.correction_brief)
            if vr2.has_blocking_failures():
                add_warning(state, f"stack_detect: blocking assertions still failing after retry — {vr2.correction_brief}")
        except Exception as exc:
            add_warning(state, f"stack_detect: retry failed: {exc}")

    state["stack"] = model.model_dump()
    step_end(log, "2-stack_detect", "stack_detect", "ok",
             f"verification={vr.verdict}")
    return state
