import { writeFileSync, rmSync, mkdtempSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { HarnessError } from "./types.ts";
import type { ClaudeResult } from "./types.ts";
import type { HarnessLogger } from "./logger.ts";
import { spawnWithStdin } from "./spawn.ts";
import type { ExecutionCapability, ExecutionRequest, ExecutionResult, ExecutionService } from "./runner.ts";
import { EXECUTION_CAPABILITY } from "./runner.ts";

export const CLAUDE_SUPPORTED_CAPABILITIES = new Set<ExecutionCapability>([
  EXECUTION_CAPABILITY.SESSION_RESUME,
  EXECUTION_CAPABILITY.ALLOWED_TOOLS,
  EXECUTION_CAPABILITY.SYSTEM_PROMPT,
  EXECUTION_CAPABILITY.AGENT,
  EXECUTION_CAPABILITY.MCP_CONFIG,
]);

export type ClaudeOptions = {
  prompt: string;
  allowedTools?: string[];
  appendSystemPrompt?: string;
  resume?: string;
  outputFormat?: "json" | "text" | "stream-json";
  cwd?: string;
  timeoutMs?: number;
  agent?: string;
  mcpConfigs?: string[];
  model?: string;
};

export async function runClaude(
  options: ClaudeOptions,
  logger?: HarnessLogger,
): Promise<ClaudeResult> {
  const { args, tempFile } = buildArgs({ ...options, outputFormat: options.outputFormat ?? "json" });
  const result = await spawnWithStdin("claude", args, options.prompt, options.cwd, options.timeoutMs);
  if (tempFile) cleanupTemp(tempFile);

  if (logger) {
    logger.logCommand("claude", ["-p", "(stdin)", ...args.slice(1)], result);
  }

  if (result.exitCode !== 0) {
    throw new HarnessError(
      `claude -p failed (exit ${result.exitCode}): ${result.stderr}`,
    );
  }

  let parsed: ClaudeResult;
  try {
    parsed = JSON.parse(result.stdout) as ClaudeResult;
  } catch {
    throw new HarnessError(
      `claude -p の出力が不正なJSONです: ${result.stdout.slice(0, 200)}`,
    );
  }

  if (parsed.is_error) {
    throw new HarnessError(
      `claude -p returned is_error=true: ${parsed.result}`,
    );
  }

  return parsed;
}

function buildArgs(options: ClaudeOptions): { args: string[]; tempFile: string | null } {
  const args = ["-p", "-"];
  let tempFile: string | null = null;

  if (options.outputFormat) {
    args.push("--output-format", options.outputFormat);
  }

  if (options.model) {
    args.push("--model", options.model);
  }

  if (options.agent) {
    args.push("--agent", options.agent);
  }

  if (options.allowedTools && options.allowedTools.length > 0) {
    args.push("--allowedTools", options.allowedTools.join(","));
  }

  if (options.appendSystemPrompt) {
    const dir = mkdtempSync(join(tmpdir(), "harness-"));
    tempFile = join(dir, "system-prompt.txt");
    writeFileSync(tempFile, options.appendSystemPrompt, "utf-8");
    args.push("--append-system-prompt-file", tempFile);
  }

  if (options.resume) {
    args.push("--resume", options.resume);
  }

  for (const mcpConfig of options.mcpConfigs ?? []) {
    args.push("--mcp-config", mcpConfig);
  }

  return { args, tempFile };
}

function cleanupTemp(filePath: string): void {
  try {
    const dir = join(filePath, "..");
    rmSync(dir, { recursive: true, force: true });
  } catch {
    // ベストエフォート
  }
}

export function createClaudeExecutionService(defaults?: {
  name?: string;
  timeoutMs?: number;
  model?: string;
}): ExecutionService {
  return {
    name: defaults?.name ?? "claude",
    capabilities: CLAUDE_SUPPORTED_CAPABILITIES,
    async execute(request, logger) {
      const result = await runClaude(
        {
          prompt: request.prompt,
          allowedTools: request.allowedTools,
          appendSystemPrompt: request.appendSystemPrompt,
          resume: request.sessionId,
          outputFormat: "json",
          cwd: request.cwd,
          timeoutMs: request.timeoutMs ?? defaults?.timeoutMs,
          agent: request.agent,
          mcpConfigs: request.mcpConfigs,
          model: defaults?.model,
        },
        logger,
      );
      return {
        text: result.result,
        sessionId: result.session_id,
        metadata: {
          costUsd: result.total_cost_usd,
          inputTokens: result.usage.input_tokens
            + (result.usage.cache_creation_input_tokens ?? 0)
            + (result.usage.cache_read_input_tokens ?? 0),
          outputTokens: result.usage.output_tokens,
          cacheCreationInputTokens: result.usage.cache_creation_input_tokens ?? 0,
          cacheReadInputTokens: result.usage.cache_read_input_tokens ?? 0,
        },
      } satisfies ExecutionResult;
    },
  };
}
