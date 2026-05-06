# commit-clean Procedure

Strip and prevent any indicator of AI use from git commits, PRs, comments, and
any other content that reaches a cloud git repo. Pairs with the deterministic
PreToolUse(Bash) hook (`commit-clean-pre-bash.sh`); the skill provides reasoning
and ticket-context embedding, the hook is the guarantee.

---

## Why this exists

The architecture's foundational rule: **zero AI footprint in cloud git.** The
seeded `.claude/` directory is excluded via `.git/info/exclude` (per-clone, never
committed). But that protects only the seeded artifacts. Commit messages, PR
descriptions, code comments, and inline content authored during work could still
leak AI markers — co-authorship lines, "Generated with Claude" tags, robot
emojis, trailer references. This skill ensures none of that ever reaches the
cloud repo.

---

## Always-do rules

When preparing any of:
- `git commit -m "..."`
- `git tag -a -m "..."`
- `git notes (add|append|edit) -m "..."`
- `gh pr create --body "..."`
- `gh issue create --body "..."`
- `gh release create --notes "..."`
- Any code comment about authorship or generation
- Any chat/message destined for a project communication channel

**NEVER include any of:**
- `Co-Authored-By: Claude <noreply@anthropic.com>` or any variant
- `Co-Authored-By: Anthropic` or `Anthropic AI`
- `Generated with Claude Code` / `Made with Claude` / `Authored by Claude`
- `🤖` (robot emoji) — including in `:robot:` shortcode form
- `[Claude Code]` link tags or trailers
- "by Claude (Sonnet|Opus|Haiku)" attributions
- "AI-assisted", "AI-generated", "Powered by Claude/AI" — anywhere
- Any chat-style "Sure! I'll help you..." preambles in commit messages

---

## Always-do replacements

Where the convention would normally include AI attribution, substitute with the
**active ticket reference** (established by `deliver-work` Step 2):

- Trailer line: `Refs: <ticket-id>` (e.g. `Refs: SCRUM-374` or
  `Refs: AMS-20260506-001`)
- Body summary: `Implements <ticket-id>: <one-line description>`
- PR description: include the ticket reference; do not mention how it was built

The ticket reference exists for auditing and tracing — it is the canonical
substitute for AI attribution.

---

## Step-by-step (when invoked from natural language)

When the dev says *"commit this"*, *"create a PR"*, *"prepare a commit message"*:

1. **Confirm active ticket reference** — read from session context (set by
   `deliver-work` Step 2). If absent, prompt the dev to establish one or
   auto-generate via the ticket-establishment behaviour.
2. **Draft the commit message** in the project's commit-message style (read
   recent commits for style signal):
   - Subject line summarising the change
   - Body with rationale, what/why, references
   - Trailer with `Refs: <ticket>` (and any other team-required trailers like
     `Reviewed-by:`)
3. **Self-check** the draft against the always-NEVER list. If any AI marker is
   present, strip it.
4. **Surface to dev** for review before executing the git/gh command.
5. **Execute** the command. The PreToolUse hook will scan it again as a backstop
   and strip anything that slipped through.
6. **Audit-log** the commit/PR creation event with the active ticket reference.

---

## How the hook backstops the skill

`commit-clean-pre-bash.sh` is the hard guarantee. It runs on every Bash tool
call and:
- Detects git/gh commands matching the patterns above
- Pattern-matches against the always-NEVER list (regex, no LLM)
- If matches found: strips them from the command, surfaces a system message to
  the dev, allows the modified command to proceed
- If no matches: passes through

The hook is conservative — it strips known patterns. It will not catch every
possible AI tell. The skill provides the comprehensive reasoning; the hook
catches what slips through.

---

## What this skill does NOT do

- It does not write code (delegated to `deliver-work`).
- It does not push to remotes or create branches (delegated to git).
- It does not block all use of `🤖` in code (only in commit/PR/comment
  metadata).
- It does not modify code comments retroactively across the repo (that would
  be a separate audit task).

---

## Audit logging

Per `audit/schema.md`:
- `commit_clean_invoked` — invocation, ticket reference active, message draft
- `ai_marker_stripped` — pattern that was matched, source command (truncated)
- `commit_executed` — final command, ticket reference embedded
