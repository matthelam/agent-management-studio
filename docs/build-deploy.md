# Build & Deploy Intelligence

How `learn-codebase` identifies the canonical build, test, and deploy commands
for a target repo — and why this matters.

---

## Why this is a first-class concern

Most projects have **multiple ways** to build or deploy, but only **one that
truly works as the team intends**. The CI pipeline runs one command; the
README says another; a developer's local notes say a third. When Claude is
working on a codebase and needs to verify a build, deploy a change, or
understand impact, it needs to know **the canonical command** — not "any
command that arguably builds the project."

`learn-codebase` Step 3 solves this with a documentation-first, code-second,
reconcile-and-surface approach.

---

## Documentation-first

The team's stated intent lives in documentation. `learn-codebase` reads:

- `README.md`
- `CONTRIBUTING.md`
- `BUILD.md`, `DEPLOY.md`, `DEPLOYMENT.md`, `SETUP.md`, `INSTALL.md`
- `docs/**/*.md`
- `AGENT.md`, `agent-instructions.md` (project-curated agent guidance)

Extracts any documented build/test/deploy commands verbatim with their
location. Notes solution-type signals from the prose ("headless", "Sitecore",
".NET", "monorepo", etc.).

---

## Code-second

The team's actual practice lives in code. `learn-codebase` inspects:

| Source | What it reveals |
|---|---|
| `package.json` `scripts` | Canonical npm/pnpm/yarn build/test/dev/deploy targets |
| `Makefile`, `Taskfile.yml`, `justfile` | Top-level command targets |
| `*.csproj`, `*.sln`, `Directory.Build.props` | MSBuild targets and configurations |
| `pom.xml`, `build.gradle`, `gradlew` | Java/Kotlin build pipeline |
| `Dockerfile`, `docker-compose.yml`, `compose.yaml` | Container build steps |
| `turbo.json`, `nx.json`, `pnpm-workspace.yaml`, `lerna.json` | Monorepo orchestration |
| `sitecore.json`, `*.scproj`, TDS / Unicorn / SCS configs | Sitecore content serialization commands |
| `.github/workflows/*.yml`, `azure-pipelines*.yml`, `.gitlab-ci.yml`, `Jenkinsfile`, `bitbucket-pipelines.yml` | What CI actually runs — often the most authoritative signal for "what really works" |

The CI pipeline is usually **the most reliable source** for canonical
commands. If the team's CI runs `pnpm turbo run build`, that's what really
works regardless of what the README says.

---

## Solution-type classification

`registries/build-deploy-signatures.json` declares signatures for solution
types. Evaluation order matters — first match wins, with hybrid types
checked first:

1. `sitecore-content-sdk-hybrid` — Next.js + Sitecore Content SDK
2. `sitecore-xmc` — Sitecore XM Cloud (with content serialization)
3. `sitecore-jss` — Sitecore JSS app
4. `headless-monorepo-turbo` — Turborepo monorepo
5. `headless-nextjs` — Next.js (non-monorepo)
6. `dotnet-app` — .NET solution
7. `containerised` — Docker-orchestrated

For each match, the registry provides a starting set of canonical commands
appropriate to the solution type. `learn-codebase` then reconciles these
against the documented and detected commands for the specific repo.

---

## Reconciliation — "the one that truly works"

Documentation says one thing; code says another; CI says a third. Conflicts
are common. `learn-codebase`:

1. Compares documented vs code-derived vs CI-derived commands.
2. **CI is the strongest signal** — if CI green-builds with command X, X is
   the canonical command.
3. **Code is next** — `package.json scripts` are usually authoritative for
   day-to-day developer workflow.
4. **Docs are the weakest signal** — documentation often lags real practice.
5. Surface conflicts to the dev: *"README says `npm run build`; CI runs
   `pnpm turbo run build`; package.json has `build` script. Which is
   canonical for this project?"*

The dev confirms or corrects. The confirmed command becomes
`canonical_build` in `config.json.environment_snapshot.build_deploy` and is
written to seeded `build-deploy.md`.

---

## What gets captured

For each project, the seeded `build-deploy.md` records:

```markdown
# Build & Deploy — <project-name>

Solution type: <classified-type>

## Canonical commands

- **Build:** `pnpm turbo run build`
- **Test:** `pnpm turbo run test`
- **Lint:** `pnpm turbo run lint`
- **Dev:** `pnpm turbo run dev`
- **Content sync** (if Sitecore): `sitecore ser pull / sitecore ser push`
- **Deploy:** `vercel deploy --prod` (or platform-specific note)

## Prerequisites

- Node 20+
- pnpm 8+
- Vercel CLI authenticated (for deploy)
- Sitecore credentials in `.env.local` (for content sync)
- Docker (for local dev environment)

## Notes

- CI authoritative source: `.github/workflows/build.yml`
- README's `npm run build` is outdated; the team migrated to pnpm in 2025-Q3.
- The `dotnet build` invocation in `legacy/` is for the `.NET` shell only;
  not part of the day-to-day frontend workflow.
```

This is **seeded into the target's `.claude/build-deploy.md`**. The
SessionStart hook injects it into the prescriptive layer so Claude knows
the canonical commands for any work it does in the target.

---

## Solution-type-specific concerns

### Headless

Build is mostly compile/bundle. Deploy goes to a hosting platform (Vercel,
Netlify, Cloudflare Pages). Deploy commands are platform-specific:

- Vercel: `vercel deploy --prod`
- Netlify: `netlify deploy --prod`
- Cloudflare Pages: `wrangler pages deploy`

`learn-codebase` detects the deploy target from CI configs and surfaces the
appropriate command.

### .NET

Build via `dotnet build` or MSBuild. Deploy varies — IIS, Azure App Service,
container, Azure Functions. Often the deploy command is in CI rather than
runnable locally; `learn-codebase` documents this rather than fabricating a
local equivalent.

### Sitecore (CMS with content serialization)

Sitecore solutions distinguish **code build** from **content sync**. Both are
necessary; both have distinct commands. `learn-codebase` captures both
explicitly:

- `canonical_build` — for the code (`next build`, `dotnet build`)
- `canonical_content_sync` — for serialized content (`sitecore ser pull`,
  `sitecore ser push`, TDS push, Unicorn pipeline)

The `sitecore-xmc-dev` and `cms-wrapper-dev` specialists know to consider
both when planning work.

### Hybrid (Sitecore + Next.js Content SDK)

Both code and content concerns. Build typically: `next build` for the head;
content sync as a separate concern. Deploy is usually two-target — Vercel for
the head, Sitecore env for the content. `learn-codebase` documents both.

### Containerised

Build via `docker build` (or `docker compose build`). Run via `docker compose
up`. Test often runs inside containers. Deploy targets vary
(docker-host, Kubernetes, container apps).

---

## v1 conservative posture: do NOT auto-execute

`learn-codebase` v1 surfaces canonical commands and recommends the dev verify
them manually before relying on them. **It does not run the build.**

Reasons for this conservative stance:

- Real-world build commands have side effects: network calls to package
  registries, Docker pulls, file generation, port binding.
- A failed build can leave the repo in a partial state.
- Some build commands have authentication side effects (e.g. `dotnet
  publish` to a private feed).
- The dev should confirm the canonical commands match their intent before
  AMS treats them as authoritative.

v2 may add opt-in sandboxed execution (Docker-isolated, time-limited) for
low-side-effect verification. v1 stays text-only.

---

## When the dev says "build this"

After `learn-codebase` has run and seeded `build-deploy.md`, when the dev
naturally invokes a build:

1. Claude consults the seeded `build-deploy.md` (loaded by SessionStart).
2. Knows the canonical command without guessing.
3. Surfaces the command to the dev: *"I'll run `pnpm turbo run build`. OK?"*
4. On confirm, executes via Bash (subject to commit-clean and prescriptive-rules
   hooks).

This is the day-to-day payoff. No more "let me check the README ... oh wait
that's outdated ... let me check package.json ..." — the canonical command
is already known and trusted.

---

## Re-checking when build/deploy changes

When CI configs, `package.json` scripts, or other build/deploy signals
change in the target repo, the next `update` run:

1. Re-runs the build/deploy detection (Step 3-equivalent).
2. Compares against `config.json.environment_snapshot.build_deploy`.
3. Surfaces deltas to the dev via the human review gate.
4. Applies on approval; `build-deploy.md` is regenerated.

This keeps the canonical commands in sync with reality without requiring a
full `learn-codebase` rebuild.
