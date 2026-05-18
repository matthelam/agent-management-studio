import type { EventType } from './types';

export interface EventTemplate {
  /** Fields expected in payload — for documentation and validation. */
  fields: string[];
  /** Single-line human summary for query output. */
  describe: (payload: Record<string, unknown>) => string;
}

export const TEMPLATES: Record<EventType, EventTemplate> = {
  session_start:    { fields: [],                               describe: ()  => 'Session started' },
  session_end:      { fields: [],                               describe: ()  => 'Session ended' },

  invocation_start: { fields: ['target', 'ams_version'],        describe: (p) => `learn-codebase started → ${p.target}` },
  invocation_end:   { fields: ['outcome', 'steps_completed'],   describe: (p) => `learn-codebase ended: ${p.outcome} (${p.steps_completed ?? '?'} steps)` },
  step_start:       { fields: ['step_id', 'step_name'],         describe: (p) => `Step ${p.step_id}: ${p.step_name}` },
  step_end:         { fields: ['step_id', 'outcome', 'duration_ms'], describe: (p) => `Step ${p.step_id} → ${p.outcome} (${p.duration_ms}ms)` },

  file_read:        { fields: ['file'],                         describe: (p) => `Read   ${p.file}` },
  file_search:      { fields: ['pattern'],                      describe: (p) => `Search ${p.pattern}` },
  artifact_write:   { fields: ['file', 'bytes'],                describe: (p) => `Write  ${p.file}${p.bytes ? ` (${p.bytes}b)` : ''}` },
  artifact_edit:    { fields: ['file'],                         describe: (p) => `Edit   ${p.file}` },
  artifact_skip:    { fields: ['file', 'reason'],               describe: (p) => `Skip   ${p.file} — ${p.reason}` },

  git_commit:       { fields: ['msg_preview', 'branch'],        describe: (p) => `git commit  "${p.msg_preview}"${p.branch ? ` [${p.branch}]` : ''}` },
  git_push:         { fields: ['command'],                      describe: (p) => `git push    ${p.command}` },
  git_branch:       { fields: ['command'],                      describe: (p) => `git branch  ${p.command}` },
  git_operation:    { fields: ['command'],                      describe: (p) => `git         ${p.command}` },

  npm_operation:    { fields: ['command'],                      describe: (p) => `npm     ${p.command}` },
  dotnet_operation: { fields: ['command'],                      describe: (p) => `dotnet  ${p.command}` },
  build_operation:  { fields: ['command'],                      describe: (p) => `build   ${p.command}` },
  bash_operation:   { fields: ['command'],                      describe: (p) => `bash    ${p.command}` },

  http_request:     { fields: ['url'],                          describe: (p) => `curl  ${p.url}` },
  web_fetch:        { fields: ['url'],                          describe: (p) => `fetch ${p.url}` },

  agent_spawn:      { fields: ['description', 'subagent_type'], describe: (p) => `Agent [${p.subagent_type ?? '?'}] ${p.description}` },

  dependency_probe:       { fields: ['dependency', 'outcome'],  describe: (p) => `probe ${p.dependency}: ${p.outcome}` },
  dependency_remediation: { fields: ['dependency', 'action'],   describe: (p) => `remediate ${p.dependency}: ${p.action}` },

  cognitive_team_proposed: { fields: ['team'],  describe: (p) => `Team proposed: ${p.team}` },
  cognitive_team_approved: { fields: ['team'],  describe: (p) => `Team approved: ${p.team}` },
  domain_skill_generated:  { fields: ['tech'],  describe: (p) => `Skill: ${p.tech}` },
  pattern_detected:        { fields: ['id'],    describe: (p) => `Pattern #${p.id}: ${p.title ?? ''}` },
  approach_detected:       { fields: ['id'],    describe: (p) => `Approach #${p.id}: ${p.title ?? ''}` },
  prescriptive_rule_generated: { fields: ['rule_id', 'action'], describe: (p) => `Rule ${p.rule_id} (${p.action})` },
  gitignore_update:        { fields: ['entries_added'],         describe: (p) => `gitignore +${p.entries_added}` },
  claude_mem_observation_seeded: { fields: ['obs_id'],          describe: (p) => `obs #${p.obs_id} → ${p.project}` },

  human_gate: { fields: ['gate', 'decision'], describe: (p) => `Gate "${p.gate}": ${p.decision}` },
  warn:       { fields: ['message'],          describe: (p) => `WARN  ${p.message}` },
  error:      { fields: ['message', 'step'],  describe: (p) => `ERROR [step ${p.step ?? '?'}] ${p.message}` },
  tool_use:   { fields: ['tool'],             describe: (p) => `tool  ${p.tool}` },

  prompt_submitted: {
    fields: ['preview', 'length', 'hash', 'truncated'],
    describe: (p) => {
      const trunc = p.truncated ? '…' : '';
      return `[${p.length}ch] "${p.preview}${trunc}"`;
    },
  },
};

export function describe(eventType: string, payload: Record<string, unknown>): string {
  const tmpl = TEMPLATES[eventType as EventType];
  if (!tmpl) return JSON.stringify(payload).slice(0, 80);
  return tmpl.describe(payload);
}
