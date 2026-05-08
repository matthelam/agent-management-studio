"""
domain_skills — Step 7: generate domain skill SKILL.md files.

For each skill in the canonical list (from canonicalize_skills()),
calls Claude (Sonnet, structured output) to produce a DomainSkillBody,
then writes the SKILL.md to .claude/skills/<name>/SKILL.md.
"""

from __future__ import annotations

from state import GraphState, DomainSkillEntry, add_error, add_warning
from state import DomainSkillBody
from call_claude import structured
from config import SONNET, UMBRELLA_TABLE, MAX_DOMAIN_SKILLS
from logger import step_start, step_end, artifact_write


def canonicalize_skills(sweep_files: list[str], stack: dict) -> list[str]:
    """
    Deterministic Python function: maps detected signals to canonical skill names.
    Uses UMBRELLA_TABLE priority order; caps at MAX_DOMAIN_SKILLS.
    Returns a list of canonical skill names (order = detection priority).
    """
    all_text = " ".join(sweep_files).lower()
    # Include package names from stack
    for v in stack.values():
        if isinstance(v, dict):
            all_text += " " + " ".join(v.keys()).lower()

    seen: set[str] = set()
    result: list[str] = []
    for signals, canonical_name in UMBRELLA_TABLE:
        if any(sig.lower() in all_text for sig in signals):
            if canonical_name not in seen:
                seen.add(canonical_name)
                result.append(canonical_name)
                if len(result) >= MAX_DOMAIN_SKILLS:
                    break
    return result


def run(state: GraphState) -> GraphState:
    """
    Requires: state["team_gate_passed"] == True

    1. Call canonicalize_skills() to get the deterministic skill list
    2. For each skill: call structured(schema=DomainSkillBody)
    3. Write SKILL.md to <target_path>/.claude/skills/<name>/SKILL.md
    4. Append DomainSkillEntry to state["domain_skills"]
    """
    raise NotImplementedError("domain_skills not yet implemented")
