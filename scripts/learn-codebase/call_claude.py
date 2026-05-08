"""
Anthropic SDK wrapper for learn-codebase graph nodes.

Two modes:
  structured(...)  — uses tools/json_schema for Pydantic-validated output
  freetext(...)    — plain text completion (pattern / approach synthesis)

Prompt caching is applied to system prompts exceeding CACHE_MIN_TOKENS.
"""

from __future__ import annotations

import json
from typing import Any, Optional, Type, TypeVar

import anthropic
from pydantic import BaseModel

from config import SONNET, OPUS

T = TypeVar("T", bound=BaseModel)

CACHE_MIN_TOKENS = 1024   # only cache system prompts large enough to benefit
MAX_TOKENS_STRUCTURED = 4096
MAX_TOKENS_FREETEXT = 8192

_client: Optional[anthropic.Anthropic] = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def _system_blocks(system_prompt: str) -> list[dict]:
    """Wrap system prompt in a cache-control block if large enough."""
    block: dict = {"type": "text", "text": system_prompt}
    if len(system_prompt.split()) >= CACHE_MIN_TOKENS:
        block["cache_control"] = {"type": "ephemeral"}
    return [block]


# ---------------------------------------------------------------------------
# Structured output — LLM produces a validated Pydantic model instance
# ---------------------------------------------------------------------------

def structured(
    *,
    system_prompt: str,
    user_message: str,
    schema: Type[T],
    model: str = SONNET,
    max_tokens: int = MAX_TOKENS_STRUCTURED,
    max_retries: int = 2,
) -> T:
    """
    Call Claude and validate the response against a Pydantic schema.
    Uses tool_choice={"type": "tool"} to force structured JSON output.
    Retries up to max_retries times on validation failure.
    """
    client = _get_client()
    tool_def = {
        "name": "structured_output",
        "description": "Return the structured output as specified.",
        "input_schema": schema.model_json_schema(),
    }

    last_exc: Optional[Exception] = None
    for attempt in range(max_retries + 1):
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=_system_blocks(system_prompt),
            tools=[tool_def],
            tool_choice={"type": "tool", "name": "structured_output"},
            messages=[{"role": "user", "content": user_message}],
        )

        for block in response.content:
            if block.type == "tool_use" and block.name == "structured_output":
                try:
                    return schema.model_validate(block.input)
                except Exception as exc:
                    last_exc = exc
                    if attempt < max_retries:
                        user_message = (
                            f"{user_message}\n\n"
                            f"[Retry {attempt + 1}] Validation error: {exc}. "
                            "Please fix and return a valid response."
                        )
                    break

    raise ValueError(
        f"structured() failed after {max_retries + 1} attempts "
        f"for schema {schema.__name__}: {last_exc}"
    )


# ---------------------------------------------------------------------------
# Free-text output — pattern / approach synthesis nodes
# ---------------------------------------------------------------------------

def freetext(
    *,
    system_prompt: str,
    user_message: str,
    model: str = OPUS,
    max_tokens: int = MAX_TOKENS_FREETEXT,
) -> str:
    """
    Call Claude and return the raw text response.
    Used for synthesis nodes that produce markdown documents.
    """
    client = _get_client()
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=_system_blocks(system_prompt),
        messages=[{"role": "user", "content": user_message}],
    )

    parts = [block.text for block in response.content if hasattr(block, "text")]
    return "\n".join(parts).strip()


# ---------------------------------------------------------------------------
# Multi-agent fan-out helper
# ---------------------------------------------------------------------------

def run_agents(
    agents: list[tuple[str, str]],  # [(harness_name, task_instruction), ...]
    shared_context: str,
    model: str = SONNET,
    max_tokens: int = MAX_TOKENS_FREETEXT,
) -> list[dict[str, str]]:
    """
    Run each agent sequentially and collect results.
    Returns [{"harness": name, "output": text}, ...].

    NOTE: Sequential for now; can be parallelised with asyncio if needed.
    """
    from harness_loader import load_harness

    results: list[dict[str, str]] = []
    for harness_name, task_instruction in agents:
        system = load_harness(harness_name)
        user = f"{task_instruction}\n\n---\n\n{shared_context}"
        output = freetext(system_prompt=system, user_message=user, model=model, max_tokens=max_tokens)
        results.append({"harness": harness_name, "output": output})
    return results
