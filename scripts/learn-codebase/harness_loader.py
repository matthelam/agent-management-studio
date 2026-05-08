"""
Harness loader — reads AMS harness markdown files.

Each harness (empiricist, specifist, synthesizer, architect, skeptic,
pragmatist, systematist) lives in $AMS_HOME/harnesses/<name>.md.
The content is injected verbatim into the system prompt for that sub-agent.
"""

from __future__ import annotations

from pathlib import Path

from ams_home import harnesses_dir


_cache: dict[str, str] = {}


def load_harness(name: str) -> str:
    """Return raw markdown content for the named harness. Raises FileNotFoundError if missing."""
    if name in _cache:
        return _cache[name]

    path: Path = harnesses_dir() / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(
            f"Harness '{name}' not found at {path}. "
            f"Available: {[p.stem for p in harnesses_dir().glob('*.md')]}"
        )

    content = path.read_text(encoding="utf-8")
    _cache[name] = content
    return content


def available_harnesses() -> list[str]:
    """Return stems of all .md files in the harnesses directory."""
    return sorted(p.stem for p in harnesses_dir().glob("*.md"))


def clear_cache() -> None:
    _cache.clear()
