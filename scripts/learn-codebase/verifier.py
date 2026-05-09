"""
Verification infrastructure for learn-codebase graph nodes.

verify() runs a single structured LLM call (using the verifier harness)
that evaluates a list of pre-formed assertions against deterministic ground
truth evidence. Nodes call this after their own LLM output is produced,
before returning state.

Design principle: assertions are defined in Python (deterministic), the LLM
only executes them against provided evidence. The LLM cannot change what is
being checked — only whether the claim passes or fails.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel

from call_claude import structured
from config import SONNET
from harness_loader import load_harness


# ---------------------------------------------------------------------------
# Assertion — defined by nodes in Python, never by the LLM
# ---------------------------------------------------------------------------

@dataclass
class Assertion:
    id: str
    description: str   # what is being checked
    evidence: str      # deterministic ground truth data
    claim: str         # what the LLM output asserts
    severity: str      # "blocking" | "warning"


# ---------------------------------------------------------------------------
# Pydantic schemas for the structured verifier LLM call
# ---------------------------------------------------------------------------

class AssertionResult(BaseModel):
    assertion_id: str
    verdict: Literal["pass", "fail", "unclear"]
    reason: str


class VerifierOutput(BaseModel):
    """Schema the verifier LLM populates — one result per assertion."""
    assertions_evaluated: list[AssertionResult]
    correction_brief: str   # empty when all pass; specific fixes when any fail


# ---------------------------------------------------------------------------
# VerificationResult — returned to nodes
# ---------------------------------------------------------------------------

@dataclass
class VerificationResult:
    step: str
    verdict: Literal["pass", "partial", "fail"]
    failed_blocking: int
    failed_warnings: int
    assertions: list[AssertionResult]
    correction_brief: str

    def passed(self) -> bool:
        return self.verdict == "pass"

    def has_blocking_failures(self) -> bool:
        return self.failed_blocking > 0

    def as_dict(self) -> dict:
        return {
            "step": self.step,
            "verdict": self.verdict,
            "failed_blocking": self.failed_blocking,
            "failed_warnings": self.failed_warnings,
            "assertions": [
                {
                    "id": a.assertion_id,
                    "verdict": a.verdict,
                    "reason": a.reason,
                }
                for a in self.assertions
            ],
            "correction_brief": self.correction_brief,
        }


# ---------------------------------------------------------------------------
# Verdict derivation — pure Python
# ---------------------------------------------------------------------------

def _derive_verdict(
    results: list[AssertionResult],
    assertion_map: dict[str, Assertion],
) -> tuple[Literal["pass", "partial", "fail"], int, int]:
    failed_blocking = sum(
        1 for r in results
        if r.verdict == "fail"
        and assertion_map.get(r.assertion_id, Assertion("", "", "", "", "warning")).severity == "blocking"
    )
    failed_warnings = sum(
        1 for r in results
        if r.verdict == "fail"
        and assertion_map.get(r.assertion_id, Assertion("", "", "", "", "blocking")).severity == "warning"
    )
    if failed_blocking > 0:
        verdict: Literal["pass", "partial", "fail"] = "fail"
    elif failed_warnings > 0:
        verdict = "partial"
    else:
        verdict = "pass"
    return verdict, failed_blocking, failed_warnings


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def verify(
    step: str,
    assertions: list[Assertion],
    model: str = SONNET,
) -> VerificationResult:
    """
    Evaluate all assertions in a single structured LLM call using the
    verifier harness. Returns a VerificationResult with per-assertion
    verdicts and an overall verdict derived deterministically.

    The verifier LLM only evaluates claims against evidence — it cannot
    change what the assertions check.
    """
    system = load_harness("verifier")

    assertion_block = "\n\n".join(
        f"[{a.id}] SEVERITY: {a.severity.upper()}\n"
        f"Description: {a.description}\n"
        f"Evidence: {a.evidence}\n"
        f"Claim: {a.claim}"
        for a in assertions
    )

    user = (
        f"Step: {step}\n\n"
        f"Evaluate every assertion below. "
        f"Return one AssertionResult per assertion_id — do not skip any.\n\n"
        f"{assertion_block}"
    )

    output = structured(
        system_prompt=system,
        user_message=user,
        schema=VerifierOutput,
        model=model,
    )

    assertion_map = {a.id: a for a in assertions}
    verdict, failed_blocking, failed_warnings = _derive_verdict(
        output.assertions_evaluated, assertion_map
    )

    return VerificationResult(
        step=step,
        verdict=verdict,
        failed_blocking=failed_blocking,
        failed_warnings=failed_warnings,
        assertions=output.assertions_evaluated,
        correction_brief=output.correction_brief,
    )
