"""
pattern_detect — Step 4a: multi-agent pattern scanning.

Three sub-agents (systematist, specifist, pragmatist) scan the codebase
from their distinct perspectives. An Opus synthesizer produces patterns.md.
"""

from __future__ import annotations

import json
from pathlib import Path

from state import GraphState, has_fatal_error, add_error
from call_claude import run_agents, freetext
from config import SONNET, OPUS, PATTERN_DETECT_AGENTS, PATTERN_SYNTHESIS_INSTRUCTION
from stub_helpers import is_stub, STUB_PATTERNS_MD
from logger import step_start, step_end, artifact_write as log_artifact_write


_MAX_FILES_PER_PKG = 3
_MAX_TOTAL_CHARS = 120_000


def _smart_sample(files: list[str], target: Path) -> str:
    """
    Option B sampling: up to 3 source files per package directory,
    prioritising barrel files (index.ts/js) and component files.
    Skips lock files, binaries, and generated files.
    """
    skip_suffixes = {".lock", ".png", ".jpg", ".jpeg", ".gif", ".svg",
                     ".woff", ".woff2", ".ttf", ".eot", ".ico", ".map"}
    skip_names = {"yarn.lock", "package-lock.json", "pnpm-lock.yaml"}
    skip_dirs = {"node_modules", ".git", "dist", "build", ".next", "out"}

    by_pkg: dict[str, list[Path]] = {}
    for abs_path in files:
        p = Path(abs_path)
        if p.suffix.lower() in skip_suffixes or p.name in skip_names:
            continue
        if any(part in skip_dirs for part in p.parts):
            continue
        pkg = str(p.parent)
        by_pkg.setdefault(pkg, []).append(p)

    selected: list[Path] = []
    for pkg_files in by_pkg.values():
        # Prioritise index/barrel files
        ordered = sorted(pkg_files, key=lambda p: (
            0 if p.stem.lower() in ("index", "barrel") else 1,
            p.name,
        ))
        selected.extend(ordered[:_MAX_FILES_PER_PKG])

    parts: list[str] = []
    total = 0
    for p in selected:
        try:
            content = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = str(p.relative_to(target)) if p.is_relative_to(target) else str(p)
        chunk = f"=== {rel} ===\n{content}\n"
        if total + len(chunk) > _MAX_TOTAL_CHARS:
            break
        parts.append(chunk)
        total += len(chunk)

    return "\n".join(parts)


def run(state: GraphState) -> GraphState:
    if has_fatal_error(state):
        return state

    meta = state["meta"]
    log = meta["log_file"]

    step_start(log, "4a-pattern_detect", "pattern_detect")

    if is_stub(state):
        state["patterns_md"] = STUB_PATTERNS_MD
        step_end(log, "4a-pattern_detect", "pattern_detect", "ok", "stub")
        return state

    sweep = state.get("sweep")
    if not sweep:
        return add_error(state, "pattern_detect", "sweep missing", fatal=True)

    target = Path(meta["target_path"])
    shared_context = _smart_sample(sweep["files_read"], target)

    stack_summary = json.dumps(state.get("stack") or {}, indent=2)
    shared_context = f"STACK:\n{stack_summary}\n\n---\n\n{shared_context}"

    try:
        agent_results = run_agents(PATTERN_DETECT_AGENTS, shared_context, model=SONNET)
        combined = "\n\n---\n\n".join(
            f"### {r['harness'].upper()} REPORT\n\n{r['output']}"
            for r in agent_results
        )
        synthesis_prompt = PATTERN_SYNTHESIS_INSTRUCTION
        patterns_md = freetext(
            system_prompt=synthesis_prompt,
            user_message=f"Three agent reports to synthesise:\n\n{combined}",
            model=OPUS,
        )
        state["patterns_md"] = patterns_md
    except Exception as exc:
        return add_error(state, "pattern_detect", str(exc), fatal=True)

    step_end(log, "4a-pattern_detect", "pattern_detect", "ok")
    return state
