"""
build_deploy — Step 3: detect canonical build, test, and deploy commands.

Pre-extracts pkg_scripts from deterministic_facts to give the verifier
ground truth for BD-002/BD-003. Passes solution_type from det_facts as
confirmed context so the LLM doesn't contradict structural file evidence.

After the LLM call the verifier checks BD-001 (solution_type) as blocking
and BD-002/BD-003/BD-004 as warnings. One retry fires on blocking failure.
"""

from __future__ import annotations

import json
from pathlib import Path

from state import GraphState, has_fatal_error, add_error, add_warning, BuildDeployModel
from call_claude import structured
from deterministic_facts import DeterministicFacts
from verifier import verify, Assertion
from config import SONNET
from stub_helpers import is_stub, stub_build_deploy
from logger import step_start, step_end, verification_result as log_vr


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


def _build_assertions(det: DeterministicFacts, model: BuildDeployModel) -> list[Assertion]:
    script_names = list(det.pkg_scripts.keys())
    ci_keywords = ["deploy", "publish", "release", "push", "upload"]

    build_cmd = model.canonical_build.strip()
    test_cmd  = model.canonical_test.strip()

    def _cmd_matches_script(cmd: str) -> bool:
        for name in script_names:
            if name in cmd:
                return True
        return False

    def _cmd_uses_ci_keyword(cmd: str) -> bool:
        cmd_lower = cmd.lower()
        return any(kw in cmd_lower for kw in ci_keywords)

    return [
        Assertion(
            id="BD-001",
            description="Detected solution_type is consistent with structural files present",
            evidence=(
                f"Deterministic inference: {det.inferred_solution_type or 'ambiguous'}. "
                f"Structural signals: sitecore.json={det.has_sitecore_json}, "
                f"turbo.json={det.has_turbo_json}, "
                f"pnpm-workspace.yaml={det.has_pnpm_workspace}, "
                f"nx.json={det.has_nx_json}"
            ),
            claim=f"LLM detected solution_type: {model.solution_type}",
            severity="blocking",
        ),
        Assertion(
            id="BD-002",
            description="canonical_build command corresponds to a script present in package.json",
            evidence=f"package.json scripts available: {json.dumps(script_names)}",
            claim=f"LLM canonical_build: '{build_cmd}'",
            severity="warning",
        ),
        Assertion(
            id="BD-003",
            description="canonical_test command corresponds to a script present in package.json",
            evidence=f"package.json scripts available: {json.dumps(script_names)}",
            claim=f"LLM canonical_test: '{test_cmd}'",
            severity="warning",
        ),
        Assertion(
            id="BD-004",
            description=(
                "canonical_deploy command is consistent with CI/CD infrastructure detected — "
                "should reference a deployment keyword or CI pipeline command"
            ),
            evidence=(
                f"Deploy-related keywords expected: {ci_keywords}. "
                f"package.json scripts: {json.dumps(script_names)}"
            ),
            claim=f"LLM canonical_deploy: '{model.canonical_deploy.strip()}'",
            severity="warning",
        ),
    ]


def _llm_call(system: str, user: str) -> BuildDeployModel:
    return structured(
        system_prompt=system,
        user_message=user,
        schema=BuildDeployModel,
        model=SONNET,
    )


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

    # Reconstruct deterministic facts (set by stack_detect)
    det = DeterministicFacts.from_dict(state.get("det_facts") or {})

    ci_content = _sample_ci(sweep["files_read"], target)

    confirmed = (
        f"Confirmed facts extracted directly from files (do not contradict these):\n"
        f"  inferred_solution_type: {det.inferred_solution_type or 'ambiguous — use your judgement'}\n"
        f"  has_sitecore_json: {det.has_sitecore_json}\n"
        f"  has_turbo_json: {det.has_turbo_json}\n"
        f"  has_pnpm_workspace: {det.has_pnpm_workspace}\n"
        f"  has_nx_json: {det.has_nx_json}\n"
        f"  package_manager: {det.package_manager or 'unknown'}\n"
        f"  pkg_scripts: {json.dumps(list(det.pkg_scripts.keys()))}\n"
    )

    system = (
        "You are a build-system analyst. Given project CI/CD and build files, "
        "identify the canonical build, test, and deploy commands along with any "
        "deployment prerequisites or known conflicts."
    )
    user = f"{confirmed}\n\nCI/CD and build files:\n\n{ci_content}"

    try:
        model = _llm_call(system, user)
    except Exception as exc:
        return add_error(state, "build_deploy", str(exc), fatal=True)

    # --- Verify ---
    assertions = _build_assertions(det, model)
    vr = verify("build_deploy", assertions)
    state["verification_results"]["build_deploy"] = vr.as_dict()
    log_vr(log, "build_deploy", vr.verdict,
           vr.failed_blocking, vr.failed_warnings, vr.correction_brief)

    # --- Retry on blocking failure ---
    if vr.has_blocking_failures():
        retry_user = (
            f"{user}\n\n"
            f"[VERIFICATION FAILED] Correction required:\n{vr.correction_brief}"
        )
        try:
            model = _llm_call(system, retry_user)
            vr2 = verify("build_deploy_retry", _build_assertions(det, model))
            state["verification_results"]["build_deploy_retry"] = vr2.as_dict()
            log_vr(log, "build_deploy_retry", vr2.verdict,
                   vr2.failed_blocking, vr2.failed_warnings, vr2.correction_brief)
            if vr2.has_blocking_failures():
                add_warning(state, f"build_deploy: blocking assertions still failing after retry — {vr2.correction_brief}")
        except Exception as exc:
            add_warning(state, f"build_deploy: retry failed: {exc}")

    state["build_deploy"] = model.model_dump()
    step_end(log, "3-build_deploy", "build_deploy", "ok",
             f"verification={vr.verdict}")
    return state
