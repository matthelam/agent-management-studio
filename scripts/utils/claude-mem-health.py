"""
claude-mem lifecycle manager.

Tiered resolution — tries each tier before falling back:
  1. HTTP ping  — worker already running at 127.0.0.1:37777 (global or local)
  2. Binary on PATH — claude-mem visible globally; start worker and re-ping
  3. Local node_modules — AMS-local install exists; start worker and re-ping
  4. npm install → npx claude-mem install --no-auto-start → start → re-ping
  5. failed — warn and skip (non-fatal)

"Healthy" means the HTTP worker at port 37777 responds, not just that the
binary is executable. The worker is what add-observation actually talks to.

Usage:
  python claude-mem-health.py            → print state, exit 0 if healthy
  python claude-mem-health.py --ensure   → attempt remediation, exit 0 if healthy
"""

from __future__ import annotations

import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

AMS_HOME = Path(__file__).resolve().parents[2]
NODE_MODULES_BIN = AMS_HOME / "node_modules" / ".bin"
_WIN = sys.platform == "win32"
# npm creates .cmd wrappers on Windows; bare name is a Unix shell script
CLAUDE_MEM_LOCAL = NODE_MODULES_BIN / ("claude-mem.cmd" if _WIN else "claude-mem")
WORKER_URL = "http://127.0.0.1:37777/api/health"


def _run(cmd: list[str], cwd: Path | None = None, timeout: int = 30) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            cwd=str(cwd) if cwd else None, timeout=timeout,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError:
        return 1, "", "executable not found"
    except subprocess.TimeoutExpired:
        return 1, "", "timeout"


def ping_worker() -> bool:
    """Return True if the HTTP worker responds at port 37777."""
    try:
        with urllib.request.urlopen(WORKER_URL, timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


def _global_bin() -> list[str] | None:
    """Return command list for a globally accessible claude-mem, or None."""
    code, _, _ = _run(["claude-mem", "--version"])
    if code == 0:
        return ["claude-mem"]
    # Also try via npx (resolves from local node_modules or npx cache)
    code, _, _ = _run(["npx", "--no-install", "claude-mem", "--version"])
    if code == 0:
        return ["npx", "--no-install", "claude-mem"]
    return None


def _local_bin() -> list[str] | None:
    """Return command list for the AMS-local install, or None."""
    if CLAUDE_MEM_LOCAL.exists():
        return [str(CLAUDE_MEM_LOCAL)]
    return None


def _start_worker(cmd: list[str]) -> bool:
    """Fire claude-mem start and wait up to 8 s for the HTTP worker to respond."""
    print("[claude-mem-health] Starting worker ...", flush=True)
    subprocess.Popen(
        cmd + ["start"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(8):
        time.sleep(1)
        if ping_worker():
            return True
    return False


def _npm_install() -> bool:
    """Run npm install in AMS_HOME. Returns True if local binary now exists."""
    print("[claude-mem-health] Running npm install ...", flush=True)
    code, _, err = _run(["npm", "install"], cwd=AMS_HOME, timeout=120)
    if code != 0:
        print(f"[claude-mem-health] npm install failed: {err}", file=sys.stderr)
        return False
    return CLAUDE_MEM_LOCAL.exists()


def _full_install() -> bool:
    """Run npx claude-mem install --no-auto-start for first-time setup."""
    print("[claude-mem-health] Running claude-mem install ...", flush=True)
    code, _, err = _run(
        ["npx", "claude-mem", "install", "--no-auto-start"],
        cwd=AMS_HOME, timeout=300,
    )
    if code != 0:
        print(f"[claude-mem-health] claude-mem install failed: {err}", file=sys.stderr)
        return False
    return True


def determine_state() -> str:
    """Return one of: healthy | start-global | start-local | install | failed."""
    if ping_worker():
        return "healthy"
    if _global_bin() is not None:
        return "start-global"
    if _local_bin() is not None:
        return "start-local"
    if (AMS_HOME / "package.json").exists():
        return "install"
    return "failed"


def ensure_healthy() -> str:
    """Walk the tier ladder until healthy or exhausted. Returns final state."""
    # Tier 1: already running
    if ping_worker():
        return "healthy"

    # Tier 2: global binary available — just start the worker
    cmd = _global_bin()
    if cmd:
        print(f"[claude-mem-health] Found global binary: {cmd[0]}", flush=True)
        if _start_worker(cmd):
            return "healthy"

    # Tier 3: local node_modules binary — start the worker
    cmd = _local_bin()
    if cmd:
        print("[claude-mem-health] Found local binary", flush=True)
        if _start_worker(cmd):
            return "healthy"

    # Tier 4a: package.json present but not installed — npm install first
    if not CLAUDE_MEM_LOCAL.exists() and (AMS_HOME / "package.json").exists():
        if not _npm_install():
            return "failed"
        cmd = _local_bin()
        if cmd and _start_worker(cmd):
            return "healthy"

    # Tier 4b: binary present but worker not responding after start — full install
    cmd = _local_bin() or (_global_bin() and [_global_bin()[0]])
    if cmd:
        print("[claude-mem-health] Worker failed to start — attempting full install", flush=True)
        if _full_install() and _start_worker(cmd):
            return "healthy"

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
