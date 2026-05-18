"""
validate_config — standalone validator for config.json.

Called as a pre-commit script and by the graph's assemble_manifest node.
Exits non-zero (fatal) if content_hashes contain "pending-first-write" values.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def validate(config_path: str) -> list[str]:
    """Return a list of error strings. Empty list = valid."""
    errors: list[str] = []

    try:
        data = json.loads(Path(config_path).read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return [f"Cannot parse config.json: {exc}"]

    hashes = data.get("content_hashes", {})
    for key, val in hashes.items():
        if val == "pending-first-write":
            errors.append(
                f"content_hashes['{key}'] = 'pending-first-write' — "
                "graph did not complete assemble_manifest"
            )

    required_keys = {"stack", "build_deploy", "cognitive_team", "domain_skills", "content_hashes"}
    missing = required_keys - set(data.keys())
    if missing:
        errors.append(f"config.json missing required keys: {sorted(missing)}")

    return errors


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path/to/config.json>", file=sys.stderr)
        sys.exit(2)

    errors = validate(sys.argv[1])
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"OK: {sys.argv[1]} is valid")


if __name__ == "__main__":
    main()
