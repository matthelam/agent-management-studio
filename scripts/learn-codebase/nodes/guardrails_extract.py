"""
guardrails_extract — Step 5: structured extraction of guard rails from approaches.md.

Replaces guardrails_parse. Instead of regex-parsing free-text markdown, a
structured LLM call extracts guard rail candidates as typed objects. The
verifier then checks extracted paths against the file sweep, catching the
silent zero-extraction failure that plagued the regex approach.

On blocking verification failure the node retries once with the correction
brief. After retry it surfaces a warning (non-fatal) so the pipeline
continues with whatever was extracted rather than halting.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from state import GraphState, GuardRail, has_fatal_error, add_warning
from call_claude import structured
from verifier import verify, Assertion
from config import SONNET
from logger import step_start, step_end, prescriptive_rule_generated, verification_result as log_vr
from stub_helpers import is_stub


# ---------------------------------------------------------------------------
# Pydantic schema for the extraction LLM call
# ---------------------------------------------------------------------------

class ExtractedGuardRailItem(BaseModel):
    path_glob: str
    action: Literal["block", "read_only", "modify_with_caution"]
    reason: str


class ExtractedGuardRailList(BaseModel):
    guard_rails: list[ExtractedGuardRailItem]
    no_guard_rails_reason: str = ""   # must explain why if list is empty


# ---------------------------------------------------------------------------
# Action mapping → GuardRail TypedDict format
# ---------------------------------------------------------------------------

_ACTION_MAP = {
    "block":               "block",
    "read_only":           "block",
    "modify_with_caution": "warn",
}

_TOOLS_MAP = {
    "block":               ["Edit", "Write", "Bash", "MultiEdit"],
    "read_only":           ["Edit", "Write", "MultiEdit"],
    "modify_with_caution": ["Edit", "Write", "MultiEdit"],
}


def _to_guard_rail(item: ExtractedGuardRailItem) -> GuardRail:
    action = _ACTION_MAP[item.action]
    tools  = _TOOLS_MAP[item.action]
    rule_id = hashlib.sha256(
        f"{item.path_glob}:{action}".encode()
    ).hexdigest()[:12]
    return GuardRail(
        id=rule_id,
        tools=tools,
        match={"path_glob": item.path_glob},
        action=action,
        reason=item.reason,
    )


# ---------------------------------------------------------------------------
# Assertion builder
# ---------------------------------------------------------------------------

_CONSTRAINT_WORDS = [
    "never", "always", "do not", "block", "caution",
    "read only", "must not", "forbidden",
]


def _build_assertions(
    extracted: ExtractedGuardRailList,
    approaches_md: str,
    sweep_files: list[str],
    target: Path,
) -> list[Assertion]:
    constraint_count = sum(
        approaches_md.lower().count(w) for w in _CONSTRAINT_WORDS
    )
    guard_rail_mentions = approaches_md.upper().count("GUARD RAIL")

    sweep_dirs = sorted({
        str(Path(f).parent).replace("\\", "/")
        for f in sweep_files
    })[:40]

    return [
        Assertion(
            id="GR-001",
            description=(
                "Guard rail list is non-empty when approaches_md contains "
                "constraint language or GUARD RAIL sections"
            ),
            evidence=(
                f"'GUARD RAIL' mentions in approaches_md: {guard_rail_mentions}. "
                f"Constraint word signals "
                f"({', '.join(_CONSTRAINT_WORDS)}): {constraint_count} occurrences."
            ),
            claim=(
                f"Extracted {len(extracted.guard_rails)} guard rails. "
                f"Empty reason: '{extracted.no_guard_rails_reason}'"
            ),
            severity="blocking",
        ),
        Assertion(
            id="GR-002",
            description=(
                "Every path glob in extracted guard rails corresponds to a real "
                "path or directory present in the file sweep"
            ),
            evidence=f"Directories present in sweep (sample): {sweep_dirs}",
            claim=f"Guard rail path globs: {[gr.path_glob for gr in extracted.guard_rails]}",
            severity="blocking",
        ),
        Assertion(
            id="GR-003",
            description=(
                "Guard rail actions fit the path type: shared packages and "
                "generated output → block or read_only; "
                "config and env files → modify_with_caution"
            ),
            evidence=(
                "Convention: published/shared packages and auto-generated "
                "artefacts are read-only; config files tolerate cautious edits"
            ),
            claim=f"Action assignments: {[(gr.path_glob, gr.action) for gr in extracted.guard_rails]}",
            severity="warning",
        ),
        Assertion(
            id="GR-004",
            description=(
                "Each guard rail has a project-specific reason, "
                "not a generic placeholder"
            ),
            evidence=(
                "Reasons must reference actual project context "
                "(package names, roles, detected patterns) — "
                "not template phrases like 'extracted from approaches.md'"
            ),
            claim=f"Reasons: {[gr.reason[:80] for gr in extracted.guard_rails]}",
            severity="warning",
        ),
    ]


# ---------------------------------------------------------------------------
# Extraction helper (used for initial call and retry)
# ---------------------------------------------------------------------------

_SYSTEM = (
    "You are extracting guard rail rules from a software architecture document. "
    "A guard rail is a constraint on AI agent behaviour — a path or file pattern "
    "that agents must treat as read-only, blocked, or modify-with-caution. "
    "Extract all guard rail candidates stated or implied in the document as "
    "structured data. If none exist, explain why in no_guard_rails_reason."
)


def _extract(user: str) -> ExtractedGuardRailList:
    return structured(
        system_prompt=_SYSTEM,
        user_message=user,
        schema=ExtractedGuardRailList,
        model=SONNET,
    )


# ---------------------------------------------------------------------------
# Node entry point
# ---------------------------------------------------------------------------

def run(state: GraphState) -> GraphState:
    if has_fatal_error(state):
        return state

    approaches_md = state.get("approaches_md") or ""
    if not approaches_md or is_stub(state):
        return state

    meta = state["meta"]
    log  = meta["log_file"]
    target = Path(meta["target_path"])
    sweep  = state.get("sweep")
    sweep_files = sweep["files_read"] if sweep else []

    step_start(log, "5-guardrails_extract", "guardrails_extract")

    user = (
        "Extract all guard rail candidates from this approaches document. "
        "For each, provide: the path_glob, the action "
        "(block / read_only / modify_with_caution), and a project-specific reason.\n\n"
        f"{approaches_md}"
    )

    try:
        extracted = _extract(user)
    except Exception as exc:
        add_warning(state, f"guardrails_extract: extraction call failed: {exc}")
        step_end(log, "5-guardrails_extract", "guardrails_extract", "warn", "extraction failed")
        return state

    # --- Verify ---
    assertions = _build_assertions(extracted, approaches_md, sweep_files, target)
    vr = verify("guardrails_extract", assertions)
    state["verification_results"]["guardrails_extract"] = vr.as_dict()
    log_vr(log, "guardrails_extract", vr.verdict,
           vr.failed_blocking, vr.failed_warnings, vr.correction_brief)

    # --- Retry on blocking failure ---
    if vr.has_blocking_failures():
        retry_user = (
            f"{user}\n\n"
            f"[VERIFICATION FAILED] Correction required:\n{vr.correction_brief}"
        )
        try:
            extracted = _extract(retry_user)
            vr2 = verify("guardrails_extract_retry", assertions)
            state["verification_results"]["guardrails_extract_retry"] = vr2.as_dict()
            log_vr(log, "guardrails_extract_retry", vr2.verdict,
                   vr2.failed_blocking, vr2.failed_warnings, vr2.correction_brief)

            if vr2.has_blocking_failures():
                add_warning(
                    state,
                    f"guardrails_extract: blocking assertions still failing after retry "
                    f"— {vr2.correction_brief}",
                )
        except Exception as exc:
            add_warning(state, f"guardrails_extract: retry failed: {exc}")

    # --- Convert to GuardRail TypedDicts ---
    rails = [_to_guard_rail(item) for item in extracted.guard_rails]
    state["guard_rails"] = rails
    state["guard_rails_parse_warnings"] = [
        f"{a.assertion_id}: {a.reason}"
        for a in vr.assertions
        if a.verdict == "fail"
    ]

    for r in rails:
        prescriptive_rule_generated(
            log, r["id"], r["match"]["path_glob"], r["action"], r["tools"]
        )

    step_end(
        log, "5-guardrails_extract", "guardrails_extract", "ok",
        f"{len(rails)} rails, verification={vr.verdict}",
    )
    return state
