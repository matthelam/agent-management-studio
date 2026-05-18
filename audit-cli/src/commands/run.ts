import { randomUUID } from 'crypto';
import { homedir } from 'os';
import { mkdirSync } from 'fs';
import { join } from 'path';
import { insertRun, updateRun, getRun, listRuns } from '../db';
import { getState, setState } from '../state';
import type { RunRecord } from '../types';

export function runStart(args: { target?: string; project?: string }): void {
  const id = randomUUID();
  const now = new Date().toISOString();

  const logsDir = join(homedir(), '.ams', 'logs');
  mkdirSync(logsDir, { recursive: true });

  // Timestamp in filename is filesystem-safe (colons replaced)
  const stamp = now.replace(/:/g, '-').replace(/\..+$/, '');
  const logFile = join(logsDir, `run-${stamp}-${id.slice(0, 8)}.jsonl`);

  const run: RunRecord = {
    id,
    project:    args.project ?? null,
    target:     args.target ?? null,
    started_at: now,
    ended_at:   null,
    outcome:    null,
    log_file:   logFile,
  };

  insertRun(run);
  setState({ active_run_id: id, active_log_file: logFile });

  // Print in a shell-sourceable format so callers can capture RUN_ID
  console.log(`RUN_ID=${id}`);
  console.log(`LOG=${logFile}`);
}

export function runEnd(args: { run?: string; outcome?: string }): void {
  const state = getState();
  const runId = args.run ?? state.active_run_id;

  if (!runId) {
    console.error('No active run and no --run <id> supplied.');
    process.exit(1);
  }

  updateRun(runId, {
    ended_at: new Date().toISOString(),
    outcome:  (args.outcome as RunRecord['outcome']) ?? 'success',
  });

  if (state.active_run_id === runId) {
    setState({ active_run_id: null, active_log_file: null });
  }

  console.log(`Run ${runId.slice(0, 8)} ended: ${args.outcome ?? 'success'}`);
}

export function runStatus(): void {
  const state = getState();
  if (!state.active_run_id) {
    console.log('No active run.');
    return;
  }
  const run = getRun(state.active_run_id);
  console.log(JSON.stringify(run, null, 2));
}

export function runList(): void {
  const runs = listRuns(20);
  if (!runs.length) { console.log('No runs found.'); return; }
  const pad = (s: string, n: number) => s.slice(0, n).padEnd(n);
  console.log(`${'ID'.padEnd(10)}  ${'STARTED'.padEnd(24)}  ${'STATUS'.padEnd(10)}  TARGET`);
  console.log('─'.repeat(80));
  for (const r of runs) {
    const status = r.ended_at ? (r.outcome ?? 'done') : 'running';
    console.log(`${pad(r.id, 10)}  ${pad(r.started_at, 24)}  ${pad(status, 10)}  ${r.target ?? '—'}`);
  }
}
