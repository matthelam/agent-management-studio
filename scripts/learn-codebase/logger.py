"""
JSONL event logger for the learn-codebase graph.

Replaces the bash emit_event sidecar from the original SKILL.md.
Every graph action writes a structured event to the run log file.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Event types
# ---------------------------------------------------------------------------

EVENT_TYPES = frozenset({
    "invocation_start",
    "invocation_end",
    "step_start",
    "step_end",
    "dependency_probe",
    "artifact_write",
    "pattern_detected",
    "approach_detected",
    "prescriptive_rule_generated",
    "human_gate",
    "verification_result",
    "warn",
    "error",
    "checkpoint_write",
    "checkpoint_resume",
})


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _write(log_file: str, event: dict) -> None:
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(event) + "\n")


# ---------------------------------------------------------------------------
# Public emit functions
# ---------------------------------------------------------------------------

def emit(log_file: str, event_type: str, **kwargs: Any) -> None:
    """Write a single JSONL event. Unknown event_types are accepted (extensible)."""
    event = {"ts": _now(), "event": event_type, **kwargs}
    _write(log_file, event)


def invocation_start(log_file: str, run_id: str, target_path: str, flags: list[str]) -> None:
    emit(log_file, "invocation_start",
         run_id=run_id, target_path=target_path, flags=flags)


def invocation_end(log_file: str, run_id: str, outcome: str,
                   observations_seeded: int, observation_failures: int,
                   errors: list[dict]) -> None:
    emit(log_file, "invocation_end",
         run_id=run_id, outcome=outcome,
         observations_seeded=observations_seeded,
         observation_failures=observation_failures,
         errors=errors)


def step_start(log_file: str, step: str, node: str) -> None:
    emit(log_file, "step_start", step=step, node=node)


def step_end(log_file: str, step: str, node: str,
             outcome: str, detail: Optional[str] = None) -> None:
    event: dict = {"step": step, "node": node, "outcome": outcome}
    if detail:
        event["detail"] = detail
    emit(log_file, "step_end", **event)


def dependency_probe(log_file: str, artifact: str, found: bool,
                     path: Optional[str] = None) -> None:
    emit(log_file, "dependency_probe",
         artifact=artifact, found=found, path=path)


def artifact_write(log_file: str, artifact: str, path: str,
                   size_bytes: Optional[int] = None) -> None:
    emit(log_file, "artifact_write",
         artifact=artifact, path=path, size_bytes=size_bytes)


def pattern_detected(log_file: str, pattern: str, confidence: str,
                     evidence_files: list[str]) -> None:
    emit(log_file, "pattern_detected",
         pattern=pattern, confidence=confidence, evidence_files=evidence_files)


def approach_detected(log_file: str, approach: str, confidence: str,
                      guard_rail_candidate: bool) -> None:
    emit(log_file, "approach_detected",
         approach=approach, confidence=confidence,
         guard_rail_candidate=guard_rail_candidate)


def prescriptive_rule_generated(log_file: str, rule_id: str, path_glob: str,
                                action: str, tools: list[str]) -> None:
    emit(log_file, "prescriptive_rule_generated",
         rule_id=rule_id, path_glob=path_glob, action=action, tools=tools)


def human_gate(log_file: str, gate: str, state: str,
               prompt_shown: Optional[str] = None,
               response: Optional[str] = None) -> None:
    emit(log_file, "human_gate",
         gate=gate, state=state,
         prompt_shown=prompt_shown, response=response)


def warn(log_file: str, step: str, message: str) -> None:
    emit(log_file, "warn", step=step, message=message)


def error(log_file: str, step: str, message: str, fatal: bool = True) -> None:
    emit(log_file, "error", step=step, message=message, fatal=fatal)


def checkpoint_write(log_file: str, gate: str, checkpoint_path: str) -> None:
    emit(log_file, "checkpoint_write", gate=gate, checkpoint_path=checkpoint_path)


def checkpoint_resume(log_file: str, gate: str, response: str) -> None:
    emit(log_file, "checkpoint_resume", gate=gate, response=response)


def verification_result(
    log_file: str,
    step: str,
    verdict: str,
    failed_blocking: int,
    failed_warnings: int,
    correction_brief: str,
) -> None:
    emit(
        log_file, "verification_result",
        step=step,
        verdict=verdict,
        failed_blocking=failed_blocking,
        failed_warnings=failed_warnings,
        correction_brief=correction_brief,
    )
