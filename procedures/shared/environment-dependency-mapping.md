# Agent-to-Environment Dependency Mapping

Each agent profile declares which environment elements it depends on. This mapping determines which agents are affected when an environment element changes.

---

## Purpose

When the diff engine detects that `react` changed from 18 to 19, the system needs to know: which agents care? The `environment_dependencies` array on each agent answers that question.

---

## Schema

Each agent in the `assembly.agents` array of `config.json` includes:

```json
{
  "name": "frontend-dev",
  "environment_dependencies": ["react", "next", "tailwindcss", "typescript", "zustand"]
}
```

The values in `environment_dependencies` are **keys** that match keys in the `environment_snapshot` sections: `runtime`, `frameworks`, `testing.runner`, `testing.e2e`, `linting`, and `key_dependencies`.

---

## Auto-Population Rules

During `/init` Step 2 (Select Specialists), dependencies are derived from the agent's specialist knowledge and the detected stack:

| Agent Type | Dependency Sources | Example Dependencies |
|------------|-------------------|---------------------|
| **frontend-dev** | Frontend frameworks, styling tools, state management, frontend testing | `react`, `next`, `tailwindcss`, `zustand`, `typescript`, `vitest` |
| **backend-dev** | Backend frameworks, runtime, ORMs, backend testing | `node`, `express`, `prisma`, `typescript`, `vitest` |
| **code-review** | All frameworks and linting tools (reviews code across the stack) | `eslint`, `prettier`, `typescript`, all detected frameworks |
| **security-audit** | Backend frameworks, runtime, auth-related dependencies | `node`, `express`, `prisma`, security-sensitive dependencies |
| **Generated specialists** | Derived from the technology they were generated for | Based on scan data used to create the specialist |

### Derivation Logic

1. Read the agent's specialist template to identify which technologies it references (via version-conditional rules and scope)
2. Match those technologies against keys in the `environment_snapshot`
3. Add any project-specific `key_dependencies` that fall within the agent's scope
4. Include `linting` tools for agents that write or review code

### Shared Dependencies

Some environment elements are shared across multiple agents:

| Element | Shared By |
|---------|-----------|
| `typescript` | All agents that write or review TypeScript code |
| `eslint` / `prettier` | All agents that write code + code-review |
| Runtime (`node`, `python`, etc.) | All agents that produce or review code in that runtime |

---

## Manual Override

The auto-populated mapping is a best guess. The human can edit `environment_dependencies` directly in `config.json` to:

- Add dependencies the auto-detection missed
- Remove dependencies that are not relevant to the agent's actual work
- Adjust after project conventions change

Manual edits are preserved across `/update` runs — the update flow modifies agent profiles but does not overwrite manually edited dependency arrays unless the human explicitly approves.

---

## Lookup Direction

The mapping supports reverse lookup:

- **Forward:** "What does this agent depend on?" → read the agent's `environment_dependencies`
- **Reverse:** "Which agents depend on this element?" → scan all agents' `environment_dependencies` for the element key

The reverse lookup is used by the change-to-agent resolution logic (see `change-to-agent-resolution.md`) to determine which agents are affected by a specific environment change.
