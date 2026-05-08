"""
Dynamic AMS_HOME resolver.

Resolves to the root of the AMS checkout at import time — no hardcoded paths.
The scripts/learn-codebase/ package lives two levels below the AMS root:
  <AMS_ROOT>/scripts/learn-codebase/ams_home.py  →  parents[2] = <AMS_ROOT>
"""

from pathlib import Path

AMS_HOME: Path = Path(__file__).resolve().parents[2]


def get_ams_home() -> Path:
    return AMS_HOME


def harnesses_dir() -> Path:
    return AMS_HOME / "harnesses"


def templates_dir() -> Path:
    return AMS_HOME / "templates"


def registries_dir() -> Path:
    return AMS_HOME / "registries"


def logs_dir() -> Path:
    d = AMS_HOME / "logs"
    d.mkdir(exist_ok=True)
    return d


def artifact_dir(run_id: str) -> Path:
    d = logs_dir() / f".run-{run_id}"
    d.mkdir(exist_ok=True)
    return d
