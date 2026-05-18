import { Database } from 'bun:sqlite';
import { homedir } from 'os';
import { mkdirSync, appendFileSync } from 'fs';
import { join } from 'path';
import type { AuditEvent, RunRecord } from './types';

const AMS_DIR = join(homedir(), '.ams');
mkdirSync(AMS_DIR, { recursive: true });

const DB_PATH = join(AMS_DIR, 'events.db');

let _db: Database | null = null;

function db(): Database {
  if (_db) return _db;
  _db = new Database(DB_PATH);
  _db.exec(`
    CREATE TABLE IF NOT EXISTS runs (
      id         TEXT PRIMARY KEY,
      project    TEXT,
      target     TEXT,
      started_at TEXT NOT NULL,
      ended_at   TEXT,
      outcome    TEXT,
      log_file   TEXT
    );

    CREATE TABLE IF NOT EXISTS events (
      id          INTEGER PRIMARY KEY AUTOINCREMENT,
      run_id      TEXT,
      session_id  TEXT,
      event_type  TEXT    NOT NULL,
      ts          TEXT    NOT NULL,
      payload     TEXT    NOT NULL,
      created_at  INTEGER NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_events_run     ON events(run_id);
    CREATE INDEX IF NOT EXISTS idx_events_type    ON events(event_type);
    CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at);
    CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id);
  `);
  return _db;
}

// ── Runs ──────────────────────────────────────────────────────────────────────

export function insertRun(run: RunRecord): void {
  db().prepare(`
    INSERT INTO runs (id, project, target, started_at, ended_at, outcome, log_file)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `).run(run.id, run.project, run.target, run.started_at, run.ended_at, run.outcome, run.log_file);
}

export function updateRun(id: string, updates: Partial<Omit<RunRecord, 'id'>>): void {
  const entries = Object.entries(updates).filter(([k]) => k !== 'id');
  if (!entries.length) return;
  const set = entries.map(([k]) => `${k} = ?`).join(', ');
  const vals = entries.map(([, v]) => v);
  db().prepare(`UPDATE runs SET ${set} WHERE id = ?`).run(...vals, id);
}

export function getRun(id: string): RunRecord | null {
  return db().prepare('SELECT * FROM runs WHERE id = ?').get(id) as RunRecord | null;
}

export function listRuns(limit = 20): RunRecord[] {
  return db().prepare('SELECT * FROM runs ORDER BY started_at DESC LIMIT ?').all(limit) as RunRecord[];
}

// ── Events ────────────────────────────────────────────────────────────────────

export function insertEvent(event: AuditEvent): void {
  db().prepare(`
    INSERT INTO events (run_id, session_id, event_type, ts, payload, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
  `).run(
    event.run_id,
    event.session_id,
    event.event_type,
    event.ts,
    JSON.stringify(event.payload),
    event.created_at,
  );
}

export function appendToJsonl(logFile: string, event: AuditEvent): void {
  const line = JSON.stringify({
    event: event.event_type,
    ts:    event.ts,
    run:   event.run_id,
    session: event.session_id,
    ...event.payload,
  });
  appendFileSync(logFile, line + '\n');
}

export interface QueryOpts {
  run_id?:     string;
  event_type?: string;
  session_id?: string;
  project?:    string;
  since?:      number;  // epoch ms
  limit?:      number;
}

export function queryEvents(opts: QueryOpts): AuditEvent[] {
  const conds: string[] = [];
  const params: unknown[] = [];

  if (opts.run_id)     { conds.push('e.run_id = ?');      params.push(opts.run_id); }
  if (opts.event_type) { conds.push('e.event_type = ?');  params.push(opts.event_type); }
  if (opts.session_id) { conds.push('e.session_id = ?');  params.push(opts.session_id); }
  if (opts.project)    { conds.push('r.project = ?');     params.push(opts.project); }
  if (opts.since)      { conds.push('e.created_at >= ?'); params.push(opts.since); }

  const where = conds.length ? `WHERE ${conds.join(' AND ')}` : '';
  const limit = opts.limit ?? 100;

  const rows = db().prepare(`
    SELECT e.*
    FROM   events e
    LEFT JOIN runs r ON e.run_id = r.id
    ${where}
    ORDER BY e.created_at ASC
    LIMIT ?
  `).all(...params, limit) as Record<string, unknown>[];

  return rows.map(r => ({
    id:         r.id as number,
    run_id:     r.run_id as string | null,
    session_id: r.session_id as string | null,
    event_type: r.event_type as AuditEvent['event_type'],
    ts:         r.ts as string,
    payload:    JSON.parse(r.payload as string),
    created_at: r.created_at as number,
  }));
}
