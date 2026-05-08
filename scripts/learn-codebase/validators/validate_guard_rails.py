"""
validate_guard_rails — standalone validator for prescriptive-rules.json.

Checks that every rule has required fields and that action values are
in the canonical set.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

VALID_ACTIONS = frozenset({"block", "warn", "allow"})
REQUIRED_RULE_KEYS = {"id", "tools", "match", "action", "reason"}


def validate(rules_path: str) -> list[str]:
    errors: list[str] = []

    try:
        data = json.loads(Path(rules_path).read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"Cannot parse prescriptive-rules.json: {exc}"]

    rules = data.get("rules", [])
    if not isinstance(rules, list):
        return ["'rules' must be a list"]

    for i, rule in enumerate(rules):
        missing = REQUIRED_RULE_KEYS - set(rule.keys())
        if missing:
            errors.append(f"rule[{i}] missing keys: {sorted(missing)}")
        if rule.get("action") not in VALID_ACTIONS:
            errors.append(
                f"rule[{i}] invalid action '{rule.get('action')}', "
                f"must be one of {sorted(VALID_ACTIONS)}"
            )
        if not isinstance(rule.get("tools", None), list):
            errors.append(f"rule[{i}] 'tools' must be a list")

    return errors


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path/to/prescriptive-rules.json>", file=sys.stderr)
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
