"""
claude-mem lifecycle manager.

Four states:
  healthy  — claude-mem responds to 'claude-mem --version'
  start    — claude-mem installed but server not running; auto-start attempted
  install  — claude-mem not found; local npm install attempted
  failed   — install or start failed; seeding step will be skipped (warn, non-fatal)

Local install: npm install is run inside AMS_HOME (not global) so the
path remains predictable and does not require admin rights.

Usage:
  python claude-mem-health.py            → print state and exit 0 if healthy
  python claude-mem-health.py --ensure   → attempt install/start if not healthy,
                                           exit 0 if healthy after remediation,
                                           exit 1 if still failed
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# Two levels up from scripts/utils/  →  AMS_HOME
AMS_HOME = Path(__file__).resolve().parents[2]
NODE_MODULES_BIN = AMS_HOME / "node_modules" / ".bin"
CLAUDE_MEM_BIN = NODE_MODULES_BIN / "claude-mem"


def _run(cmd: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=str(cwd) if cwd else None
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def _bin_path() -> Path | None:
    """Return path to claude-mem binary if it exists."""
    if CLAUDE_MEM_BIN.exists():
        return CLAUDE_MEM_BIN
    # Fall back to PATH lookup
    code, out, _ = _run(["claude-mem", "--version"])
    if code == 0:
        return Path("claude-mem")  # on PATH
    return None


def check_healthy() -> bool:
    """Return True if claude-mem responds successfully."""
    bin_path = _bin_path()
    if bin_path is None:
        return False
    code, _, _ = _run([str(bin_path), "--version"])
    return code == 0


def install() -> bool:
    """Run npm install in AMS_HOME to add claude-mem locally. Returns True on success."""
    print("[claude-mem-health] Running npm install in AMS_HOME ...", flush=True)
    code, out, err = _run(["npm", "install"], cwd=AMS_HOME)
    if code != 0:
        print(f"[claude-mem-health] npm install failed: {err}", file=sys.stderr)
        return False
    return CLAUDE_MEM_BIN.exists()


def start_server() -> bool:
    """Attempt to start the claude-mem server. Returns True if it becomes healthy."""
    bin_path = _bin_path()
    if bin_path is None:
        return False
    print("[claude-mem-health] Starting claude-mem server ...", flush=True)
    subprocess.Popen(
        [str(bin_path), "start"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    import time
    for _ in range(5):
        time.sleep(1)
        if check_healthy():
            return True
    return False


def determine_state() -> str:
    """Return one of: healthy | start | install | failed."""
    if check_healthy():
        return "healthy"
    if _bin_path() is not None:
        return "start"
    if (AMS_HOME / "package.json").exists():
        return "install"
    return "failed"


def ensure_healthy() -> str:
    """Try to reach healthy state. Returns final state string."""
    state = determine_state()
    if state == "healthy":
        return "healthy"
    if state == "install":
        if install():
            state = "start"
        else:
            return "failed"
    if state == "start":
        if start_server():
            return "healthy"
        return "failed"
    return "failed"


def main() -> None:
    ensure = "--ensure" in sys.argv

    if ensure:
        final_state = ensure_healthy()
        print(f"[claude-mem-health] state={final_state}")
        sys.exit(0 if final_state == "healthy" else 1)
    else:
        state = determine_state()
        print(f"[claude-mem-health] state={state}")
        sys.exit(0 if state == "healthy" else 1)


if __name__ == "__main__":
    main()
