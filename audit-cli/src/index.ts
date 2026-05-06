#!/usr/bin/env bun
import { runStart, runEnd, runStatus, runList } from './commands/run';
import { emitEvent, emitFromStdin } from './commands/emit';
import { query, queryRun } from './commands/query';

const argv = process.argv.slice(2);
const cmd  = argv[0];
const sub  = argv[1];

// ── Arg parsing helpers ───────────────────────────────────────────────────────

function flags(args: string[]): Record<string, string> {
  const out: Record<string, string> = {};
  for (let i = 0; i < args.length; i++) {
    if (args[i].startsWith('--') && !args[i].includes('=')) {
      const key = args[i].slice(2);
      out[key] = args[i + 1] ?? 'true';
      i++;
    } else if (args[i].startsWith('--') && args[i].includes('=')) {
      const [k, ...v] = args[i].slice(2).split('=');
      out[k] = v.join('=');
    }
  }
  return out;
}

/** --field key=value  repeated flags → payload object */
function fields(args: string[]): Record<string, string> {
  const out: Record<string, string> = {};
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--field' && args[i + 1]) {
      const eq = args[i + 1].indexOf('=');
      if (eq > -1) {
        const k = args[i + 1].slice(0, eq);
        const v = args[i + 1].slice(eq + 1);
        out[k] = v;
      }
      i++;
    }
  }
  return out;
}

// ── Commands ──────────────────────────────────────────────────────────────────

switch (cmd) {

  // ── run ──
  case 'run': {
    const f = flags(argv.slice(2));
    switch (sub) {
      case 'start':  runStart({ target: f.target, project: f.project }); break;
      case 'end':    runEnd({ run: f.run, outcome: f.outcome }); break;
      case 'status': runStatus(); break;
      case 'list':   runList(); break;
      default:
        console.error('Usage: ams-audit run start|end|status|list');
        process.exit(1);
    }
    break;
  }

  // ── emit ──
  // Two call paths:
  //   1. Flag-based (SKILL.md bash preamble):
  //      ams-audit emit step_start --field step_id=4 --field step_name=cognitive-team
  //   2. Stdin JSON (hook scripts — avoids shell quoting issues with arbitrary values):
  //      echo '{"type":"artifact_write","payload":{"file":"foo.ts"}}' | ams-audit emit
  case 'emit': {
    if (!sub) {
      // No subcommand → stdin JSON mode
      await emitFromStdin();
      break;
    }
    const f  = flags(argv.slice(2));
    const pl = fields(argv.slice(2));
    emitEvent({ type: sub, session: f.session, run: f.run, payload: pl });
    break;
  }

  // ── query ──
  case 'query': {
    const f = flags(argv.slice(1));
    if (f.run && argv[1] !== '--run') {
      // ams-audit query <run-id> shorthand
      queryRun(argv[1]);
    } else {
      query({
        run:     f.run,
        type:    f.type,
        session: f.session,
        project: f.project,
        since:   f.since,
        limit:   f.limit ? parseInt(f.limit, 10) : undefined,
        json:    f.json === 'true',
      });
    }
    break;
  }

  // ── help ──
  default: {
    console.log(`
ams-audit — AMS deterministic audit logger

COMMANDS
  run start  [--target <path>] [--project <name>]    Start a new run, set active
  run end    [--run <id>] [--outcome success|failure] End the active (or named) run
  run status                                          Show active run details
  run list                                            List recent runs

  emit <type> [--session <id>] [--run <id>]          Emit an event (flag mode)
            [--field key=value ...]
  emit                                                Emit from stdin JSON
    echo '{"type":"...","payload":{...}}' | ams-audit emit

  query [--run <id>] [--type <event-type>]            Query events (table output)
        [--project <name>] [--session <id>]
        [--since <ISO|epochMs>] [--limit N] [--json]

EVENT TYPES
  session_start / session_end
  invocation_start / invocation_end
  step_start / step_end
  file_read / file_search
  artifact_write / artifact_edit / artifact_skip
  git_commit / git_push / git_branch / git_operation
  npm_operation / dotnet_operation / bash_operation
  http_request / web_fetch
  agent_spawn
  dependency_probe / dependency_remediation
  cognitive_team_proposed / cognitive_team_approved
  domain_skill_generated / pattern_detected / approach_detected
  prescriptive_rule_generated / gitignore_update
  claude_mem_observation_seeded
  human_gate / warn / error

DATABASE
  ~/.ams/events.db   — SQLite queue
  ~/.ams/logs/       — per-run JSONL files
  ~/.ams/state.json  — active run pointer
`);
    break;
  }
}
