import { homedir } from 'os';
import { join } from 'path';
import { existsSync, readFileSync, writeFileSync } from 'fs';
import type { AmsState } from './types';

const STATE_PATH = join(homedir(), '.ams', 'state.json');

export function getState(): AmsState {
  if (!existsSync(STATE_PATH)) return { active_run_id: null, active_log_file: null };
  try {
    return JSON.parse(readFileSync(STATE_PATH, 'utf-8')) as AmsState;
  } catch {
    return { active_run_id: null, active_log_file: null };
  }
}

export function setState(state: AmsState): void {
  writeFileSync(STATE_PATH, JSON.stringify(state, null, 2));
}
