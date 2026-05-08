"""
AMS dependency setup — idempotent, local-only.

Ensures both dependency stacks are installed before running any AMS script:
  npm  → node_modules/ at AMS root       (claude-mem and any future JS tools)
  pip  → scripts/learn-codebase/.venv/   (langgraph, anthropic SDK, pydantic)

Fast when already done: only runs installers when sentinel files are absent.
Safe to run on every SessionStart — no side effects when up-to-date.

Usage:
  python scripts/setup.py          # install only
  python scripts/setup.py --check  # print status, exit 1 if anything missing
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

AMS_HOME = Path(__file__).resolve().parent.parent
LEARN_CODEBASE = AMS_HOME / "scripts" / "learn-codebase"

# Sentinels — presence means the install is done
_WIN = sys.platform == "win32"
NPM_SENTINEL = AMS_HOME / "node_modules" / ".bin" / ("claude-mem.cmd" if _WIN else "claude-mem")
VENV_PYTHON   = LEARN_CODEBASE / ".venv" / ("Scripts" if _WIN else "bin") / ("python.exe" if _WIN else "python")
REQUIREMENTS  = LEARN_CODEBASE / "requirements.txt"


def _run(cmd: list[str], cwd: Path) -> int:
    print(f"  $ {' '.join(cmd)}", flush=True)
    return subprocess.run(cmd, cwd=str(cwd)).returncode


def ensure_npm() -> bool:
    """Install node_modules if claude-mem sentinel is absent. Returns True if healthy."""
    if NPM_SENTINEL.exists():
        return True
    print("[setup] node_modules missing — running npm install ...", flush=True)
    rc = _run(["npm", "install"], cwd=AMS_HOME)
    if rc != 0:
        print(f"[setup] ERROR: npm install failed (exit {rc})", file=sys.stderr)
        return False
    if not NPM_SENTINEL.exists():
        print("[setup] ERROR: npm install completed but sentinel not found", file=sys.stderr)
        return False
    print("[setup] npm install OK", flush=True)
    return True


def ensure_venv() -> bool:
    """Create venv and pip-install requirements if venv python is absent. Returns True if healthy."""
    if VENV_PYTHON.exists():
        return True
    if not REQUIREMENTS.exists():
        print(f"[setup] ERROR: requirements.txt not found at {REQUIREMENTS}", file=sys.stderr)
        return False

    print("[setup] Python venv missing — creating ...", flush=True)
    rc = _run([sys.executable, "-m", "venv", str(LEARN_CODEBASE / ".venv")], cwd=AMS_HOME)
    if rc != 0:
        print(f"[setup] ERROR: venv creation failed (exit {rc})", file=sys.stderr)
        return False

    print("[setup] Installing pip requirements ...", flush=True)
    rc = _run([str(VENV_PYTHON), "-m", "pip", "install", "-r", str(REQUIREMENTS),
               "--quiet"], cwd=LEARN_CODEBASE)
    if rc != 0:
        print(f"[setup] ERROR: pip install failed (exit {rc})", file=sys.stderr)
        return False

    print("[setup] Python venv OK", flush=True)
    return True


def check_status() -> dict[str, bool]:
    return {
        "npm (node_modules)": NPM_SENTINEL.exists(),
        "pip (learn-codebase venv)": VENV_PYTHON.exists(),
    }


def main() -> None:
    check_only = "--check" in sys.argv

    if check_only:
        status = check_status()
        all_ok = True
        for name, ok in status.items():
            mark = "OK  " if ok else "MISS"
            print(f"  [{mark}] {name}")
            if not ok:
                all_ok = False
        sys.exit(0 if all_ok else 1)

    npm_ok  = ensure_npm()
    venv_ok = ensure_venv()

    if npm_ok and venv_ok:
        print("[setup] All dependencies ready.", flush=True)
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
