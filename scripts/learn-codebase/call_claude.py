"""
Claude CLI subprocess wrapper for learn-codebase graph nodes.

Replaces the Anthropic SDK so the pipeline runs inside the user's existing
Claude Code session — no separate API key needed.

Two modes:
  structured(...)  — template-based JSON output validated against a Pydantic model
  freetext(...)    — plain text completion (pattern / approach synthesis)

The --json-schema CLI flag is broken in current Claude Code versions (returns
empty result), so structured output uses a template approach: a fill-in-the-blank
JSON object is embedded in the prompt and Claude is asked to populate it.
"""

from __future__ import annotations

import json
import re
import subprocess
from typing import Any, Optional, Type, TypeVar

from pydantic import BaseModel

from config import SONNET, OPUS

T = TypeVar("T", bound=BaseModel)

_TIMEOUT_STRUCTURED = 180   # seconds — structured calls with schema in prompt
_TIMEOUT_FREETEXT   = 540   # seconds — synthesis nodes generate longer output
_TIMEOUT_AGENT      = 600   # seconds — per-agent scan of a large codebase
_MAX_RETRIES        = 2


# ---------------------------------------------------------------------------
# Core subprocess helper
# ---------------------------------------------------------------------------

def _run_claude(
    prompt: str,
    *,
    system_prompt: str = "",
    model: str = SONNET,
    timeout: int = _TIMEOUT_STRUCTURED,
) -> str:
    """
    Invoke `claude -p` headless and return the text result.

    The prompt is passed via stdin (not -p arg) to avoid Windows CreateProcess
    command-line length limits when prompts include large file content.
    """
    cmd = [
        "claude",
        "--output-format", "json",
        "--no-session-persistence",
        "--model", model,
    ]
    if system_prompt:
        cmd += ["--system-prompt", system_prompt]

    result = subprocess.run(
        cmd,
        input=prompt,
        capture_output=True,
        text=True,
        timeout=timeout,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"claude CLI exited {result.returncode}: {result.stderr[:400]}"
        )

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"claude CLI returned non-JSON stdout: {result.stdout[:200]}"
        ) from exc

    return data.get("result", "")


# ---------------------------------------------------------------------------
# JSON schema → fill-in-the-blank template
# ---------------------------------------------------------------------------

def _schema_to_template(schema: dict[str, Any], defs: dict[str, Any] | None = None) -> Any:
    """
    Recursively convert a JSON schema dict to a fill-in-the-blank template.

    The returned value is JSON-serialisable; placeholder strings like
    "<string: description>" tell Claude what type and meaning each field has.
    """
    if defs is None:
        defs = schema.get("$defs", {})

    # Resolve $ref first
    if "$ref" in schema:
        ref_name = schema["$ref"].split("/")[-1]
        return _schema_to_template(defs.get(ref_name, {}), defs)

    # Use schema default when present (catches Optional[X]=None → null,
    # and fixed-value fields like schema_version=1)
    if "default" in schema and "properties" not in schema and "items" not in schema:
        default_val = schema["default"]
        # Only use default for scalars and null; recurse for objects/arrays
        if not isinstance(default_val, (dict, list)) or default_val is None:
            return default_val

    # anyOf / oneOf — pick first non-null option
    for compound_key in ("anyOf", "oneOf"):
        if compound_key in schema:
            non_null = [s for s in schema[compound_key] if s.get("type") != "null"]
            if non_null:
                return _schema_to_template(non_null[0], defs)
            return None

    t = schema.get("type")
    desc = schema.get("description", "")
    enum = schema.get("enum")

    if enum is not None:
        return f"<one_of: {' | '.join(str(e) for e in enum)}>"

    if t == "object" or "properties" in schema:
        props = schema.get("properties", {})
        if props:
            return {k: _schema_to_template(v, defs) for k, v in props.items()}
        # dict[str, X] — additionalProperties style
        add = schema.get("additionalProperties", {})
        val_hint = add.get("type", "value") if isinstance(add, dict) else "value"
        return {"<key>": f"<{val_hint}>"}

    if t == "array":
        items = schema.get("items", {})
        return [_schema_to_template(items, defs)]

    if t == "string":
        hint = f": {desc[:80]}" if desc else ""
        return f"<string{hint}>"
    if t == "integer":
        return 0
    if t == "number":
        return 0.0
    if t == "boolean":
        return False

    return f"<{t or 'value'}>"


# ---------------------------------------------------------------------------
# Structured output — LLM fills a template; Pydantic validates the result
# ---------------------------------------------------------------------------

def structured(
    *,
    system_prompt: str,
    user_message: str,
    schema: Type[T],
    model: str = SONNET,
    max_tokens: int = 4096,     # kept for API-compatibility; CLI controls internally
    max_retries: int = _MAX_RETRIES,
) -> T:
    """
    Call Claude CLI and validate the response against a Pydantic schema.

    Embeds a fill-in-the-blank JSON template in the prompt. Claude is
    instructed to respond with ONLY a valid JSON object (no markdown fences,
    no explanation). Retries up to max_retries times on parse / validation
    failure, appending the error to the prompt so Claude can self-correct.
    """
    json_schema = schema.model_json_schema()
    template    = _schema_to_template(json_schema)

    base_prompt = (
        f"{user_message}\n\n"
        "---\n"
        "IMPORTANT: Respond with ONLY a valid JSON object. "
        "No explanation. No markdown fences. No code blocks.\n"
        "Fill in every placeholder (replace `<...>` with real values):\n"
        f"{json.dumps(template, indent=2)}"
    )

    last_exc: Optional[Exception] = None
    prompt = base_prompt

    for attempt in range(max_retries + 1):
        try:
            raw = _run_claude(prompt, system_prompt=system_prompt, model=model)
        except RuntimeError as exc:
            last_exc = exc
            break

        # Strip markdown fences if the model added them despite instructions
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```[^\n]*\n?", "", cleaned)
            cleaned = re.sub(r"\n?```\s*$", "", cleaned)
            cleaned = cleaned.strip()

        try:
            parsed = json.loads(cleaned)
            return schema.model_validate(parsed)
        except json.JSONDecodeError as exc:
            last_exc = exc
            if attempt < max_retries:
                prompt = (
                    f"{base_prompt}\n\n"
                    f"[Retry {attempt + 1}] Your previous response was not valid JSON. "
                    f"Error: {exc}. Respond with ONLY a JSON object."
                )
        except Exception as exc:
            last_exc = exc
            if attempt < max_retries:
                prompt = (
                    f"{base_prompt}\n\n"
                    f"[Retry {attempt + 1}] Validation error: {exc}. "
                    "Fix the values and respond with ONLY a valid JSON object."
                )

    raise ValueError(
        f"structured() failed after {max_retries + 1} attempts "
        f"for schema {schema.__name__}: {last_exc}"
    )


# ---------------------------------------------------------------------------
# Free-text output — synthesis nodes that produce markdown documents
# ---------------------------------------------------------------------------

def freetext(
    *,
    system_prompt: str,
    user_message: str,
    model: str = OPUS,
    max_tokens: int = 8192,     # kept for API-compatibility; CLI controls internally
) -> str:
    """
    Call Claude CLI and return the raw text response.
    Used for pattern_detect and approach_detect synthesis.
    """
    return _run_claude(
        user_message,
        system_prompt=system_prompt,
        model=model,
        timeout=_TIMEOUT_FREETEXT,
    )


# ---------------------------------------------------------------------------
# Multi-agent fan-out helper
# ---------------------------------------------------------------------------

def run_agents(
    agents: list[tuple[str, str]],  # [(harness_name, task_instruction), ...]
    shared_context: str,
    model: str = SONNET,
    max_tokens: int = 8192,         # kept for API-compatibility
) -> list[dict[str, str]]:
    """
    Run each agent sequentially and collect results.
    Returns [{"harness": name, "output": text}, ...].
    """
    from harness_loader import load_harness

    results: list[dict[str, str]] = []
    for harness_name, task_instruction in agents:
        system = load_harness(harness_name)
        user   = f"{task_instruction}\n\n---\n\n{shared_context}"
        output = _run_claude(
            user,
            system_prompt=system,
            model=model,
            timeout=_TIMEOUT_AGENT,
        )
        results.append({"harness": harness_name, "output": output})
    return results
