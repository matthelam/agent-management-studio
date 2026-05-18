"""
main.py — CLI entry point for the learn-codebase LangGraph pipeline.

Usage
-----
Fresh run:
  python main.py run <target_path> [--strict] [--thorough] [--stub-llm]

Resume from a human gate:
  python main.py resume --artifact-dir <dir> --response "<text>"

Human gates
-----------
When the graph hits a gate node (stack_gate, team_gate, or the
rebuild_confirmation in preflight) it prints the gate prompt and exits
with code 2.  The artifact directory and resume command are printed so
Claude Code can present them to the user.  After the user responds,
invoke the resume sub-command to continue.
"""

from __future__ import annotations

import argparse
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import sys as _sys
if hasattr(_sys.stdout, "reconfigure"):
    _sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from langgraph.types import Command

from ams_home import get_ams_home, artifact_dir, logs_dir
from state import RunMeta, initial_state
from checkpoint_io import write_gate_checkpoint, read_gate_checkpoint, gate_state_summary
import logger
from graph import make_graph


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_run_id() -> str:
    return uuid.uuid4().hex[:8]


def _checkpoint_db(art_dir: str) -> str:
    return str(Path(art_dir) / "checkpoint.db")


def _config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def _handle_interrupt(interrupt_value: object, art_dir: str, thread_id: str, log_file: str) -> None:
    """Print the gate prompt and write the checkpoint file."""
    # interrupt_value may be an Interrupt namedtuple or a raw dict
    raw = getattr(interrupt_value, "value", interrupt_value)
    value = raw if isinstance(raw, dict) else {"prompt": str(raw)}
    gate = value.get("gate", "unknown_gate")
    prompt = value.get("prompt", str(raw))

    write_gate_checkpoint(art_dir, gate, thread_id, prompt, {"log_file": log_file})
    logger.checkpoint_write(log_file, gate, str(Path(art_dir) / "gate-checkpoint.json"))

    sep = "=" * 64
    print(f"\n{sep}")
    print(f"  HUMAN GATE: {gate}")
    print(sep)
    print(prompt)
    print(f"\n  Artifact dir : {art_dir}")
    print(f"  Resume with  :")
    print(f'    python main.py resume --artifact-dir "{art_dir}" --response "yes"')
    print(f"{sep}\n")


# ---------------------------------------------------------------------------
# stream runner — detects interrupts from the update stream
# ---------------------------------------------------------------------------

def _stream(graph, input_val, config: dict, art_dir: str,
            thread_id: str, log_file: str) -> int:
    """
    Stream the graph and handle the first interrupt encountered.
    Returns 0 on clean completion, 2 on interrupt (human gate).

    In LangGraph 0.2.x, graph.invoke() does not raise GraphInterrupt;
    interrupts appear as {"__interrupt__": [...]} chunks in the stream.
    """
    for chunk in graph.stream(input_val, config, stream_mode="updates"):
        if "__interrupt__" in chunk:
            interrupts = chunk["__interrupt__"]
            first = interrupts[0] if interrupts else None
            if first is not None:
                _handle_interrupt(first, art_dir, thread_id, log_file)
            return 2
    return 0


# ---------------------------------------------------------------------------
# sub-commands
# ---------------------------------------------------------------------------

def cmd_run(args: argparse.Namespace) -> int:
    run_id = _make_run_id()
    target_path = str(Path(args.target_path).resolve())
    art_dir = str(artifact_dir(run_id))
    log_file = str(logs_dir() / f"{run_id}.jsonl")

    flags: list[str] = []
    if args.strict:    flags.append("--strict")
    if args.thorough:  flags.append("--thorough")
    if args.stub_llm:  flags.append("--stub-llm")

    meta = RunMeta(
        run_id=run_id,
        target_path=target_path,
        ams_home=str(get_ams_home()),
        target_basename=Path(target_path).name,
        log_file=log_file,
        artifact_dir=art_dir,
        flags=flags,
        started_at=datetime.now(tz=timezone.utc).isoformat(),
    )

    state = initial_state(meta)
    graph = make_graph(_checkpoint_db(art_dir))
    config = _config(run_id)

    logger.invocation_start(log_file, run_id, target_path, flags)
    print(f"\nlearn-codebase  run_id={run_id}")
    print(f"target : {target_path}")
    if flags:
        print(f"flags  : {' '.join(flags)}")
    print()

    return _stream(graph, state, config, art_dir, run_id, log_file)


def cmd_resume(args: argparse.Namespace) -> int:
    art_dir = args.artifact_dir
    try:
        checkpoint = read_gate_checkpoint(art_dir)
    except FileNotFoundError:
        print(f"ERROR: no gate checkpoint found in {art_dir}", file=sys.stderr)
        return 1

    thread_id = checkpoint["thread_id"]
    log_file = checkpoint.get("state_summary", {}).get("log_file", "")
    gate = checkpoint.get("gate", "unknown")

    graph = make_graph(_checkpoint_db(art_dir))
    config = _config(thread_id)

    if log_file:
        logger.checkpoint_resume(log_file, gate, args.response)

    print(f"\nResuming gate '{gate}'  thread={thread_id}")
    print(f"Response: {args.response}\n")

    return _stream(graph, Command(resume=args.response), config, art_dir, thread_id, log_file)


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="learn-codebase LangGraph pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    run_p = sub.add_parser("run", help="Start a fresh learn-codebase run")
    run_p.add_argument("target_path", help="Path to the target git repository")
    run_p.add_argument("--strict",    action="store_true",
                       help="Fail on any warning")
    run_p.add_argument("--thorough",  action="store_true",
                       help="Use full-source sampling instead of smart-sample")
    run_p.add_argument("--stub-llm",  action="store_true",
                       help="Skip real LLM calls; use stub values (for testing)")

    res_p = sub.add_parser("resume", help="Resume from a human gate")
    res_p.add_argument("--artifact-dir", required=True,
                       help="Path to the run artifact directory")
    res_p.add_argument("--response",     required=True,
                       help="User response to the gate prompt")

    args = parser.parse_args()

    if args.cmd == "run":
        sys.exit(cmd_run(args))
    elif args.cmd == "resume":
        sys.exit(cmd_resume(args))


if __name__ == "__main__":
    main()
