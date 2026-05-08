"""
GraphState and all Pydantic output models for the learn-codebase graph.

TypedDicts define the state that flows between nodes.
Pydantic models define what each LLM node must produce (validated by the SDK).
"""

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

from pydantic import BaseModel, Field, field_validator

from config import (
    VALID_HARNESSES,
    VALID_LENSES,
    VALID_SOLUTION_TYPES,
    VALID_ALTITUDE_BANDS,
    MAX_DOMAIN_SKILLS,
)


# ---------------------------------------------------------------------------
# TypedDicts — graph state components
# ---------------------------------------------------------------------------

class RunMeta(TypedDict):
    run_id:          str
    target_path:     str   # absolute, resolved at launch
    ams_home:        str   # resolved via ams_home.py
    target_basename: str   # derived from target_path
    log_file:        str   # absolute path to JSONL run log
    artifact_dir:    str   # <ams_home>/logs/.run-<run_id>/
    flags:           list[str]   # e.g. ["--strict"], ["--thorough"]
    started_at:      str   # ISO-8601


class SweepResult(TypedDict):
    files_read:   list[str]   # absolute paths
    file_count:   int
    completed_at: str


class GuardRail(TypedDict):
    id:     str              # sha256[:12] of path+action
    tools:  list[str]        # tools this rule applies to
    match:  dict             # {"path_glob": "..."} or {"command_regex": "..."}
    action: str              # "block" | "warn" | "allow"
    reason: str


class DomainSkillEntry(TypedDict):
    name:         str         # canonical umbrella name e.g. "sitecore-knowledge"
    file_path:    str         # absolute path written to target
    is_canonical: bool        # False if no umbrella match
    merged_from:  list[str]   # sub-concern signals that were merged in


# ---------------------------------------------------------------------------
# GraphState — the single typed object that flows through every node
# ---------------------------------------------------------------------------

class GraphState(TypedDict):
    # --- run metadata ---
    meta:                    RunMeta
    existing_seed_detected:  bool
    rebuild_confirmed:       bool

    # --- step artifacts ---
    sweep:        Optional[SweepResult]
    stack:        Optional[dict]          # StackSnapshotModel.model_dump() after validation
    build_deploy: Optional[dict]          # BuildDeployModel.model_dump() after validation
    patterns_md:  Optional[str]           # raw file content
    approaches_md: Optional[str]          # raw file content
    guard_rails:  list[GuardRail]
    guard_rails_parse_warnings: list[str]
    cognitive_team: Optional[dict]        # CognitiveTeamProposal.model_dump() after validation
    domain_skills:  list[DomainSkillEntry]

    # --- gate states ---
    stack_gate_passed:      bool
    stack_gate_corrections: Optional[str]
    team_gate_passed:       bool
    team_gate_corrections:  Optional[str]

    # --- seed status ---
    prescriptive_rules_written: bool
    config_json_written:        bool
    tool_safety_written:        bool
    seed_complete:              bool
    observations_seeded:        int
    observation_failures:       int

    # --- content hashes (computed in assemble_manifest) ---
    content_hashes: dict[str, str]   # {"patterns_md": "<sha256>", "approaches_md": "<sha256>"}

    # --- error + warning accumulator ---
    errors:   list[dict]    # {"step": str, "message": str, "fatal": bool}
    warnings: list[str]


def initial_state(meta: RunMeta) -> GraphState:
    """Returns a fully-initialised GraphState with safe defaults."""
    return GraphState(
        meta=meta,
        existing_seed_detected=False,
        rebuild_confirmed=False,
        sweep=None,
        stack=None,
        build_deploy=None,
        patterns_md=None,
        approaches_md=None,
        guard_rails=[],
        guard_rails_parse_warnings=[],
        cognitive_team=None,
        domain_skills=[],
        stack_gate_passed=False,
        stack_gate_corrections=None,
        team_gate_passed=False,
        team_gate_corrections=None,
        prescriptive_rules_written=False,
        config_json_written=False,
        tool_safety_written=False,
        seed_complete=False,
        observations_seeded=0,
        observation_failures=0,
        content_hashes={},
        errors=[],
        warnings=[],
    )


def has_fatal_error(state: GraphState) -> bool:
    return any(e.get("fatal") for e in state["errors"])


def add_error(state: GraphState, step: str, message: str, fatal: bool = True) -> GraphState:
    state["errors"].append({"step": step, "message": message, "fatal": fatal})
    return state


def add_warning(state: GraphState, message: str) -> GraphState:
    state["warnings"].append(message)
    return state


# ---------------------------------------------------------------------------
# Pydantic models — LLM node output schemas
# ---------------------------------------------------------------------------

class StackSnapshotModel(BaseModel):
    schema_version:   int             = Field(default=1)
    runtime:          dict[str, str]  = Field(description="e.g. {'node': '22.14.0'}")
    package_manager:  dict[str, str]  = Field(description="e.g. {'name': 'npm', 'version': '10.9.2'}")
    frameworks:       dict[str, str]  = Field(description="e.g. {'next': '^15.3.6'}")
    testing:          dict            = Field(description="{'runner': {...}, 'e2e': null}")
    linting:          dict[str, str]
    key_dependencies: dict[str, str]
    structure:        dict            = Field(
        description="type, orchestrator, apps[], packages[], platform, serialization"
    )

    @field_validator("schema_version")
    @classmethod
    def must_be_one(cls, v: int) -> int:
        if v != 1:
            raise ValueError("schema_version must be 1")
        return v

    @field_validator("runtime")
    @classmethod
    def runtime_not_empty(cls, v: dict) -> dict:
        if not v:
            raise ValueError("runtime must have at least one entry")
        return v


class BuildDeployModel(BaseModel):
    solution_type:               str            = Field(
        description=f"One of: {', '.join(sorted(VALID_SOLUTION_TYPES))}"
    )
    canonical_build:             str
    canonical_test:              str
    canonical_deploy:            str
    canonical_content_sync_push: Optional[str]  = None
    canonical_content_sync_pull: Optional[str]  = None
    prerequisites:               list[str]       = Field(default_factory=list)
    conflicts_surfaced:          list[str]       = Field(default_factory=list)

    @field_validator("solution_type")
    @classmethod
    def valid_solution_type(cls, v: str) -> str:
        if v not in VALID_SOLUTION_TYPES:
            raise ValueError(f"solution_type '{v}' not in valid set: {VALID_SOLUTION_TYPES}")
        return v

    @field_validator("canonical_build", "canonical_test", "canonical_deploy")
    @classmethod
    def non_empty_command(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("canonical command cannot be empty")
        return v.strip()


class CognitiveTeamProposal(BaseModel):
    cognitive_team: list[str] = Field(
        description=f"1-6 harness names from: {', '.join(sorted(VALID_HARNESSES))}"
    )
    primary_harness_for_single_mode: str
    audit_primary_harness:           str
    default_lenses:                  list[str] = Field(
        description=f"Subset of: {', '.join(sorted(VALID_LENSES))}"
    )
    altitude_band_default:           str       = Field(default="maker")
    synthesis_harness:               str       = Field(default="synthesizer")
    work_item_prefix:                str       = Field(
        description="2-3 uppercase letters derived from project name e.g. 'ASX'"
    )

    @field_validator("cognitive_team")
    @classmethod
    def valid_harnesses(cls, v: list[str]) -> list[str]:
        if not 1 <= len(v) <= 6:
            raise ValueError("cognitive_team must have 1-6 entries")
        invalid = set(v) - VALID_HARNESSES
        if invalid:
            raise ValueError(f"Unknown harnesses: {invalid}")
        return v

    @field_validator("primary_harness_for_single_mode", "audit_primary_harness", "synthesis_harness")
    @classmethod
    def valid_single_harness(cls, v: str) -> str:
        if v not in VALID_HARNESSES:
            raise ValueError(f"Unknown harness: '{v}'")
        return v

    @field_validator("default_lenses")
    @classmethod
    def valid_lenses(cls, v: list[str]) -> list[str]:
        invalid = set(v) - VALID_LENSES
        if invalid:
            raise ValueError(f"Unknown lenses: {invalid}")
        return v

    @field_validator("altitude_band_default")
    @classmethod
    def valid_altitude(cls, v: str) -> str:
        if v not in VALID_ALTITUDE_BANDS:
            raise ValueError(f"altitude_band_default must be one of {VALID_ALTITUDE_BANDS}")
        return v

    @field_validator("work_item_prefix")
    @classmethod
    def valid_prefix(cls, v: str) -> str:
        if not (v.isupper() and v.isalpha() and 2 <= len(v) <= 3):
            raise ValueError("work_item_prefix must be 2-3 uppercase ASCII letters")
        return v


class DomainSkillBody(BaseModel):
    name: str = Field(
        description="Canonical umbrella skill name e.g. 'sitecore-knowledge'"
    )
    frontmatter_description: str = Field(
        description="SKILL.md frontmatter description — when to invoke, "
                    "file patterns, keyword triggers"
    )
    project_specific_patterns: str = Field(
        description="Extracted relevant section from patterns.md for this tech"
    )
    project_specific_approaches: str = Field(
        description="Extracted relevant section from approaches.md for this tech, "
                    "including any GUARD RAILS"
    )
    cli_commands: str = Field(
        description="Canonical CLI commands from build_deploy relevant to this tech; "
                    "empty string if none"
    )
    mcp_methods: str = Field(
        description="MCP method invocation examples from tech-mcp-map.json; "
                    "empty string if none applicable"
    )
    doc_fallback_url:     str = Field(description="Official docs URL for this tech")
    doc_fallback_version: str = Field(description="Version in use in this project")
    storybook_mandatory_precondition: bool = Field(
        default=False,
        description="True only when name == 'storybook-knowledge'"
    )

    @field_validator("name")
    @classmethod
    def name_ends_in_knowledge(cls, v: str) -> str:
        if not v.endswith("-knowledge"):
            raise ValueError("domain skill name must end in '-knowledge'")
        return v
