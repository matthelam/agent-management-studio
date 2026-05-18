import { queryEvents, listRuns, getRun } from '../db';
import { describe } from '../templates';
import { getState } from '../state';

export interface QueryArgs {
  run?:     string;
  type?:    string;
  session?: string;
  project?: string;
  since?:   string;   // ISO string or epoch ms
  limit?:   number;
  json?:    boolean;
}

export function query(args: QueryArgs): void {
  // Resolve active run if --run not supplied
  const runId = args.run ?? (args.project ? undefined : getState().active_run_id ?? undefined);

  const since = args.since
    ? (isNaN(Number(args.since)) ? Date.parse(args.since) : Number(args.since))
    : undefined;

  const events = queryEvents({
    run_id:     runId,
    event_type: args.type,
    session_id: args.session,
    project:    args.project,
    since,
    limit:      args.limit ?? 200,
  });

  if (args.json) {
    console.log(JSON.stringify(events, null, 2));
    return;
  }

  if (!events.length) { console.log('No events found.'); return; }

  const padType = (s: string) => s.slice(0, 26).padEnd(26);
  const runRef  = (id: string | null) => id ? id.slice(0, 8) : '--------';

  console.log(`${'TIMESTAMP'.padEnd(24)}  ${'EVENT TYPE'.padEnd(26)}  ${'RUN'.padEnd(8)}  DETAIL`);
  console.log('─'.repeat(100));
  for (const e of events) {
    const detail = describe(e.event_type, e.payload);
    console.log(`${e.ts.slice(0, 23)}  ${padType(e.event_type)}  ${runRef(e.run_id)}  ${detail}`);
  }
}

export function queryRun(runId: string): void {
  const run = getRun(runId);
  if (!run) { console.log(`Run not found: ${runId}`); return; }
  console.log(JSON.stringify(run, null, 2));
}
