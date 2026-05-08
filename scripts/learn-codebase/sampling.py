"""
sampling.py — shared file-sampling utilities for pattern_detect and approach_detect.
"""

from __future__ import annotations

from pathlib import Path


_MAX_FILES_PER_PKG = 3
_MAX_TOTAL_CHARS = 120_000

_SKIP_SUFFIXES = {".lock", ".png", ".jpg", ".jpeg", ".gif", ".svg",
                  ".woff", ".woff2", ".ttf", ".eot", ".ico", ".map"}
_SKIP_NAMES = {"yarn.lock", "package-lock.json", "pnpm-lock.yaml"}
_SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", "out"}


def smart_sample(files: list[str], target: Path,
                 max_files_per_pkg: int = _MAX_FILES_PER_PKG,
                 max_total_chars: int = _MAX_TOTAL_CHARS) -> str:
    """
    Option B sampling: up to max_files_per_pkg source files per package
    directory, prioritising barrel files (index.ts/js) and component files.
    Skips lock files, binaries, and generated files.
    """
    by_pkg: dict[str, list[Path]] = {}
    for abs_path in files:
        p = Path(abs_path)
        if p.suffix.lower() in _SKIP_SUFFIXES or p.name in _SKIP_NAMES:
            continue
        if any(part in _SKIP_DIRS for part in p.parts):
            continue
        pkg = str(p.parent)
        by_pkg.setdefault(pkg, []).append(p)

    selected: list[Path] = []
    for pkg_files in by_pkg.values():
        ordered = sorted(pkg_files, key=lambda p: (
            0 if p.stem.lower() in ("index", "barrel") else 1,
            p.name,
        ))
        selected.extend(ordered[:max_files_per_pkg])

    parts: list[str] = []
    total = 0
    for p in selected:
        try:
            content = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = str(p.relative_to(target)) if p.is_relative_to(target) else str(p)
        chunk = f"=== {rel} ===\n{content}\n"
        if total + len(chunk) > max_total_chars:
            break
        parts.append(chunk)
        total += len(chunk)

    return "\n".join(parts)
