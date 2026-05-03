import type { HarnessLogger } from "./logger.ts";

export const RUNNER_CAPABILITY = {
  SESSION_RESUME: "session_resume",
  ALLOWED_TOOLS: "allowed_tools",
  SYSTEM_PROMPT: "system_prompt",
} as const;

export type RunnerCapability = (typeof RUNNER_CAPABILITY)[keyof typeof RUNNER_CAPABILITY];

export type RunnerRequest = {
  prompt: string;
  cwd?: string;
  timeoutMs?: number;
  allowedTools?: string[];
  appendSystemPrompt?: string;
  sessionId?: string;
};

export type RunnerResponse = {
  text: string;
  sessionId?: string;
  metadata?: {
    costUsd?: number | null;
    inputTokens?: number;
    outputTokens?: number;
  };
};

export type Runner = {
  readonly name: string;
  readonly capabilities: ReadonlySet<RunnerCapability>;
  run(request: RunnerRequest, logger?: HarnessLogger): Promise<RunnerResponse>;
};

export function prepareRequest(runner: Runner, request: RunnerRequest): RunnerRequest {
  const prepared = { ...request };

  if (prepared.appendSystemPrompt && !runner.capabilities.has(RUNNER_CAPABILITY.SYSTEM_PROMPT)) {
    prepared.prompt = `${prepared.prompt}\n\n---\n## Additional Context\n${prepared.appendSystemPrompt}`;
    prepared.appendSystemPrompt = undefined;
  }

  if (prepared.sessionId && !runner.capabilities.has(RUNNER_CAPABILITY.SESSION_RESUME)) {
    prepared.sessionId = undefined;
  }

  if (prepared.allowedTools && !runner.capabilities.has(RUNNER_CAPABILITY.ALLOWED_TOOLS)) {
    const writePatterns = prepared.allowedTools.filter(t => t.startsWith("Write(") || t.startsWith("Edit("));
    if (writePatterns.length > 0) {
      prepared.prompt += `\n\n## File Scope Constraint\nOnly modify files matching: ${writePatterns.join(", ")}`;
    }
    prepared.allowedTools = undefined;
  }

  return prepared;
}
