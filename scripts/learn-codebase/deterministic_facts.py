"""
Deterministic pre-extraction of project facts from manifest files.

DeterministicFacts gives stack_detect and build_deploy nodes ground truth
data that Python can read directly from the filesystem — no LLM involved.
These facts are passed as confirmed context to the LLM and later used as
evidence in verifier assertions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# Packages to track versions for in framework_versions
_FRAMEWORK_KEYS: frozenset[str] = frozenset({
    "next",
    "react",
    "vue",
    "angular",
    "nuxt",
    "typescript",
    "vite",
    "tailwindcss",
    "@sitecore-jss/sitecore-jss-nextjs",
    "@sitecore-content-sdk/nextjs",
    "@sitecore-content-sdk/react",
})


@dataclass
class DeterministicFacts:
    # Runtime
    node_version: Optional[str] = None          # from engines.node in package.json

    # Package manager — inferred from lockfile presence
    package_manager: Optional[str] = None       # "npm" | "yarn" | "pnpm"
    pm_lockfile: Optional[str] = None           # the lockfile filename that was found

    # Framework versions extracted from dependencies / devDependencies
    framework_versions: dict[str, str] = field(default_factory=dict)

    # Structural file presence flags
    has_sitecore_json: bool = False
    has_turbo_json: bool = False
    has_pnpm_workspace: bool = False
    has_nx_json: bool = False

    # Scripts from root package.json (or rendering layer when root has none)
    pkg_scripts: dict[str, str] = field(default_factory=dict)

    # Conservative deterministic solution_type inference (None = ambiguous)
    inferred_solution_type: Optional[str] = None

    def as_dict(self) -> dict:
        return {
            "node_version": self.node_version,
            "package_manager": self.package_manager,
            "pm_lockfile": self.pm_lockfile,
            "framework_versions": self.framework_versions,
            "has_sitecore_json": self.has_sitecore_json,
            "has_turbo_json": self.has_turbo_json,
            "has_pnpm_workspace": self.has_pnpm_workspace,
            "has_nx_json": self.has_nx_json,
            "pkg_scripts": self.pkg_scripts,
            "inferred_solution_type": self.inferred_solution_type,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "DeterministicFacts":
        return cls(
            node_version=d.get("node_version"),
            package_manager=d.get("package_manager"),
            pm_lockfile=d.get("pm_lockfile"),
            framework_versions=d.get("framework_versions") or {},
            has_sitecore_json=d.get("has_sitecore_json", False),
            has_turbo_json=d.get("has_turbo_json", False),
            has_pnpm_workspace=d.get("has_pnpm_workspace", False),
            has_nx_json=d.get("has_nx_json", False),
            pkg_scripts=d.get("pkg_scripts") or {},
            inferred_solution_type=d.get("inferred_solution_type"),
        )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _rel_names(sweep_files: list[str], target: Path) -> set[str]:
    result: set[str] = set()
    for f in sweep_files:
        p = Path(f)
        try:
            result.add(str(p.relative_to(target)).replace("\\", "/"))
        except ValueError:
            result.add(p.name)
    return result


def _parse_pkg(path: Path, facts: DeterministicFacts) -> bool:
    """
    Read one package.json and merge into facts.
    Returns True on success. Never raises.
    """
    try:
        pkg = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (json.JSONDecodeError, OSError):
        return False

    # Node version from engines field
    if facts.node_version is None:
        node_ver = pkg.get("engines", {}).get("node")
        if node_ver:
            facts.node_version = node_ver

    # Scripts (first package.json with scripts wins)
    if not facts.pkg_scripts:
        facts.pkg_scripts = pkg.get("scripts", {})

    # Framework versions — merge without overwriting
    all_deps: dict[str, str] = {}
    all_deps.update(pkg.get("dependencies", {}))
    all_deps.update(pkg.get("devDependencies", {}))
    for k, v in all_deps.items():
        if k in _FRAMEWORK_KEYS or any(k.startswith(fw) for fw in _FRAMEWORK_KEYS):
            facts.framework_versions.setdefault(k, v)

    return True


def _infer_solution_type(facts: DeterministicFacts, rels: set[str]) -> Optional[str]:
    """
    Conservative deterministic classification based purely on file presence.
    Returns None when the evidence is ambiguous — the verifier treats None
    as permissive (allows the LLM classification without contradiction).
    """
    has_csproj = any(r.endswith(".csproj") or r.endswith(".fsproj") for r in rels)
    has_next_config = any("next.config" in r for r in rels)

    # Sitecore + monorepo tooling
    if facts.has_sitecore_json and (facts.has_turbo_json or facts.has_pnpm_workspace):
        return "headless-monorepo-turbo"

    # Sitecore without monorepo tooling
    if facts.has_sitecore_json:
        return "sitecore-xmc"

    # Turbo or NX monorepo without Sitecore
    if facts.has_turbo_json or (facts.has_pnpm_workspace and facts.has_nx_json):
        return "headless-monorepo-turbo"

    # .NET project
    if has_csproj:
        return "dotnet-app"

    # Plain Next.js
    if has_next_config:
        return "headless-nextjs"

    return None


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def extract(sweep_files: list[str], target: Path) -> DeterministicFacts:
    """
    Parse manifest files deterministically to extract ground truth facts.
    Called before any LLM call in stack_detect; result stored in state for
    downstream nodes (build_deploy, domain_skills).
    """
    facts = DeterministicFacts()
    rels = _rel_names(sweep_files, target)

    # Structural file presence — check root AND common rendering-layer paths
    # (Sitecore monorepos keep turbo.json / workspace files under src/rendering/)
    _RENDERING_PREFIXES = ("", "src/rendering/", "rendering/")

    facts.has_sitecore_json = any(
        r == "sitecore.json" or r.endswith("/sitecore.json") for r in rels
    )
    facts.has_turbo_json = any(
        f"{pfx}turbo.json" in rels for pfx in _RENDERING_PREFIXES
    )
    facts.has_pnpm_workspace = any(
        f"{pfx}pnpm-workspace.yaml" in rels for pfx in _RENDERING_PREFIXES
    )
    facts.has_nx_json = any(
        f"{pfx}nx.json" in rels for pfx in _RENDERING_PREFIXES
    )

    # Package manager from lockfile (priority: pnpm > yarn > npm).
    # Check root first, then rendering-layer subdirectories.
    _LOCKFILE_CANDIDATES = [
        ("pnpm-lock.yaml", "pnpm"),
        ("yarn.lock",       "yarn"),
        ("package-lock.json", "npm"),
    ]
    for lockfile, pm in _LOCKFILE_CANDIDATES:
        found = next(
            (r for pfx in _RENDERING_PREFIXES if (r := f"{pfx}{lockfile}") in rels),
            None,
        )
        if found:
            facts.package_manager, facts.pm_lockfile = pm, found
            break

    # Root package.json first
    _parse_pkg(target / "package.json", facts)

    # Rendering layer fallback — common in Sitecore monorepos
    if not facts.pkg_scripts:
        for candidate in ("src/rendering/package.json", "rendering/package.json"):
            if _parse_pkg(target / candidate, facts):
                break

    facts.inferred_solution_type = _infer_solution_type(facts, rels)

    return facts
