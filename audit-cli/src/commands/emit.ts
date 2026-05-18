import { insertEvent, appendToJsonl } from '../db';
import { getState } from '../state';
import type { AuditEvent, EventType, EmitInput } from '../types';

/**
 * Core emit — called by both the CLI (flag-based) and stdin JSON path.
 * Hook scripts pipe JSON directly to stdin; the CLI SKILL.md preamble uses flags.
 */
export function emitEvent(input: EmitInput): void {
  const state = getState();
  const now = new Date().toISOString();

  const event: AuditEvent = {
    run_id:     input.run ?? state.active_run_id,
    session_id: input.session ?? null,
    event_type: input.type as EventType,
    ts:         now,
    payload:    input.payload,
    created_at: Date.now(),
  };

  insertEvent(event);

  const logFile = state.active_log_file;
  if (logFile) appendToJsonl(logFile, event);
}

/**
 * Read a full EmitInput from stdin (JSON).
 * Used by hook scripts: echo '{"type":"...","payload":{...}}' | ams-audit emit
 */
export async function emitFromStdin(): Promise<void> {
  const chunks: Buffer[] = [];
  for await (const chunk of Bun.stdin.stream()) {
    chunks.push(Buffer.from(chunk));
  }
  const raw = Buffer.concat(chunks).toString('utf-8').trim();
  if (!raw) return;

  let input: EmitInput;
  try {
    input = JSON.parse(raw) as EmitInput;
  } catch {
    process.stderr.write(`ams-audit emit: invalid JSON on stdin\n`);
    process.exit(1);
  }

  emitEvent(input);
}
