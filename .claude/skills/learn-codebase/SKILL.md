---
name: learn-codebase
description: Bootstrap or rebuild the AMS profile for a target git repository. Scans the codebase, detects the stack, identifies build & deploy commands, proposes the agent team, generates patterns.md / approaches.md / prescriptive-rules.json / per-project domain skills, then seeds everything into the target repo's .claude/ directory (excluded from git via .git/info/exclude). Use when starting AMS on a fresh repo, or to rebuild a profile from scratch.
---

# learn-codebase

Runs the deterministic LangGraph pipeline at
`scripts/learn-codebase/main.py`. All orchestration, human gates, and
LLM calls are managed by the pipeline — this skill is a launcher only.

---

## Prerequisites

- Python venv at `scripts/learn-codebase/.venv/` (created once via
  `python -m venv .venv && .venv/Scripts/pip install -r requirements.txt`)
- `ANTHROPIC_API_KEY` set, **or** written to
  `scripts/learn-codebase/.env` as `ANTHROPIC_API_KEY=sk-ant-...`
- Target must be a git repository

---

## Fresh run

```powershell
cd C:\Repositories\agent-management-studio\scripts\learn-codebase
.\.venv\Scripts\python.exe main.py run <absolute-path-to-target-repo>
```

Optional flags:
- `--strict`    — fail on any pipeline warning
- `--thorough`  — full-source sampling instead of smart-sample
- `--stub-llm`  — dry-run without real LLM calls (for testing)

---

## Human gates

The pipeline pauses at two gates and exits with code 2, printing the gate
prompt and a resume command:

1. **stack_gate** — confirms detected stack + build/deploy commands
2. **team_gate** — confirms proposed cognitive team

When a gate fires, the terminal prints:

```
  Artifact dir : <path>
  Resume with  :
    python main.py resume --artifact-dir "<path>" --response "yes"
```

Run the resume command (with `"yes"` or your corrections) to continue.

---

## Outputs

All artifacts are written to `<target>/.claude/`:

| File | Content |
|---|---|
| `config.json` | Assembly manifest (stack, team, domain skills) |
| `patterns.md` | Detected coding patterns |
| `approaches.md` | Architectural approaches + GUARD RAILS |
| `prescriptive-rules.json` | Machine-parseable guard rail rules |
| `skills/<tech>-knowledge/SKILL.md` | Per-technology domain skills |

Run log: `logs/<run-id>.jsonl` (under AMS root)
Artifact dir: `logs/.run-<run-id>/` (cleaned up on completion)
