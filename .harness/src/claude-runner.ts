import { writeFileSync, rmSync, mkdtempSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { HarnessError } from "./types.ts";
import type { ClaudeResult } from "./types.ts";
import type { HarnessLogger } from "./logger.ts";
import { spawnWithStdin } from "./spawn.ts";
import { RUNNER_CAPABILITY } from "./runner.ts";
import type { Runner, RunnerResponse } from "./runner.ts";

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

  // Claude が exit 0 でも内部エラーを報告する場合がある
  if (parsed.is_error) {
    throw new HarnessError(
      `claude -p returned is_error=true: ${parsed.result}`,
    );
  }

  return parsed;
}

function buildArgs(options: ClaudeOptions): { args: string[]; tempFile: string | null } {
  // prompt は stdin 経由で渡すので "-p" に "-" を指定
  const args = ["-p", "-"];
  let tempFile: string | null = null;

  if (options.outputFormat) {
    args.push("--output-format", options.outputFormat);
  }

  if (options.agent) {
    args.push("--agent", options.agent);
  }

  if (options.allowedTools && options.allowedTools.length > 0) {
    args.push("--allowedTools", options.allowedTools.join(","));
  }

  if (options.appendSystemPrompt) {
    // 大きな system prompt は一時ファイル経由で渡す（E2BIG 防止）
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
    // ファイルと親ディレクトリ（mkdtempSync で作成）を両方削除
    const dir = join(filePath, "..");
    rmSync(dir, { recursive: true, force: true });
  } catch {
    // ベストエフォート
  }
}

export function createClaudeRunner(defaults?: { timeoutMs?: number }): Runner {
  return {
    name: "claude",
    capabilities: new Set([
      RUNNER_CAPABILITY.SESSION_RESUME,
      RUNNER_CAPABILITY.ALLOWED_TOOLS,
      RUNNER_CAPABILITY.SYSTEM_PROMPT,
      RUNNER_CAPABILITY.AGENT,
      RUNNER_CAPABILITY.MCP_CONFIG,
    ]),
    async run(request, logger) {
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
      } satisfies RunnerResponse;
    },
  };
}
