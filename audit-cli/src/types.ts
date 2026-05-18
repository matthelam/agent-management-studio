export type EventType =
  // session lifecycle
  | 'session_start'
  | 'session_end'
  // learn-codebase run lifecycle
  | 'invocation_start'
  | 'invocation_end'
  | 'step_start'
  | 'step_end'
  // file operations
  | 'file_read'
  | 'file_search'
  | 'artifact_write'
  | 'artifact_edit'
  | 'artifact_skip'
  // git
  | 'git_commit'
  | 'git_push'
  | 'git_branch'
  | 'git_operation'
  // build / package
  | 'npm_operation'
  | 'dotnet_operation'
  | 'build_operation'
  | 'bash_operation'
  // network
  | 'http_request'
  | 'web_fetch'
  // agents
  | 'agent_spawn'
  // learn-codebase specific
  | 'dependency_probe'
  | 'dependency_remediation'
  | 'cognitive_team_proposed'
  | 'cognitive_team_approved'
  | 'domain_skill_generated'
  | 'pattern_detected'
  | 'approach_detected'
  | 'prescriptive_rule_generated'
  | 'gitignore_update'
  | 'claude_mem_observation_seeded'
  // prompt capture
  | 'prompt_submitted'
  // quality
  | 'human_gate'
  | 'warn'
  | 'error'
  // fallback
  | 'tool_use';

export interface AuditEvent {
  id?: number;
  run_id: string | null;
  session_id: string | null;
  event_type: EventType;
  ts: string;
  payload: Record<string, unknown>;
  created_at: number;
}

export interface RunRecord {
  id: string;
  project: string | null;
  target: string | null;
  started_at: string;
  ended_at: string | null;
  outcome: 'success' | 'failure' | 'stopped' | null;
  log_file: string | null;
}

export interface AmsState {
  active_run_id: string | null;
  active_log_file: string | null;
}

export interface EmitInput {
  type: string;
  session?: string;
  run?: string;
  payload: Record<string, unknown>;
}
