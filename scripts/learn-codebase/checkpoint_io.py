"""
Gate checkpoint read/write utilities.

When the graph reaches a human gate it writes a checkpoint JSON file,
then exits. Claude Code presents the gate to the user. The user responds
in the chat. Claude Code resumes the graph by calling:

  python graph.py --resume --thread-id <id> --response "<user-response>"

This module handles reading and writing those checkpoint files and
injecting the user response back into the graph state.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional


CHECKPOINT_FILENAME = "gate-checkpoint.json"


def checkpoint_path(artifact_dir: str) -> Path:
    return Path(artifact_dir) / CHECKPOINT_FILENAME


def write_gate_checkpoint(
    artifact_dir: str,
    gate: str,
    thread_id: str,
    prompt_shown: str,
    state_summary: dict[str, Any],
) -> Path:
    """
    Write a gate checkpoint file so the graph can be resumed after
    the user responds to the human gate in Claude Code chat.
    """
    data = {
        "gate": gate,
        "thread_id": thread_id,
        "prompt_shown": prompt_shown,
        "state_summary": state_summary,
        "response": None,
    }
    path = checkpoint_path(artifact_dir)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def read_gate_checkpoint(artifact_dir: str) -> dict[str, Any]:
    """Read an existing gate checkpoint. Raises FileNotFoundError if absent."""
    path = checkpoint_path(artifact_dir)
    return json.loads(path.read_text(encoding="utf-8"))


def inject_response(artifact_dir: str, response: str) -> dict[str, Any]:
    """Inject the user's resume response into the checkpoint and return updated data."""
    data = read_gate_checkpoint(artifact_dir)
    data["response"] = response
    path = checkpoint_path(artifact_dir)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def clear_checkpoint(artifact_dir: str) -> None:
    """Delete the checkpoint file after a successful gate passage."""
    path = checkpoint_path(artifact_dir)
    if path.exists():
        path.unlink()


def gate_state_summary(state: dict) -> dict[str, Any]:
    """Extract a slim summary of graph state for checkpoint display."""
    return {
        "run_id":       state["meta"]["run_id"],
        "target_path":  state["meta"]["target_path"],
        "stack":        state.get("stack"),
        "build_deploy": state.get("build_deploy"),
        "error_count":  len(state.get("errors", [])),
        "warning_count": len(state.get("warnings", [])),
    }
