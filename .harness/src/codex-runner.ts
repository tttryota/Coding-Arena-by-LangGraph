import { Codex } from "@openai/codex-sdk";
import type { ApprovalMode, Input, SandboxMode, Thread } from "@openai/codex-sdk";
import type { Runner, RunnerResponse } from "./runner.ts";
import { RUNNER_CAPABILITY } from "./runner.ts";
import type { HarnessLogger } from "./logger.ts";
import { HarnessError, RunnerRateLimitError } from "./types.ts";

function toApprovalPolicy(sandbox: string | undefined): ApprovalMode {
  if (sandbox === "danger-full-access" || sandbox === "workspace-write") {
    return "never";
  }
  return "untrusted";
}

function toSandboxMode(sandbox: string | undefined): SandboxMode {
  if (sandbox === "workspace-write" || sandbox === "danger-full-access" || sandbox === "read-only") {
    return sandbox;
  }
  return "workspace-write";
}

export function createCodexRunner(defaults?: {
  name?: string;
  timeoutMs?: number;
  sandbox?: string;
  projectRoot?: string;
}): Runner {
  const codex = new Codex();

  return {
    name: defaults?.name ?? "codex",
    capabilities: new Set([
      RUNNER_CAPABILITY.SESSION_RESUME,
    ]),
    async run(request, logger) {
      const cwd = request.cwd ?? defaults?.projectRoot;
      const timeoutMs = request.timeoutMs ?? defaults?.timeoutMs;
      const sandboxMode = toSandboxMode(defaults?.sandbox);
      const approvalPolicy = toApprovalPolicy(defaults?.sandbox);
      const thread = request.sessionId
        ? codex.resumeThread(request.sessionId, {
            sandboxMode,
            workingDirectory: cwd,
            approvalPolicy,
          })
        : codex.startThread({
            sandboxMode,
            workingDirectory: cwd,
            approvalPolicy,
          });

      try {
        return await runThread(thread, request.prompt, timeoutMs, logger);
      } catch (error: unknown) {
        const message = error instanceof Error ? error.message : String(error);
        if (/rate|limit|429/i.test(message)) {
          throw new RunnerRateLimitError("codex", message);
        }
        throw new HarnessError(`codex sdk run failed: ${message}`);
      }
    },
  };
}

async function runThread(
  thread: Thread,
  prompt: string,
  timeoutMs: number | undefined,
  logger?: HarnessLogger,
): Promise<RunnerResponse> {
  const signal = timeoutMs ? AbortSignal.timeout(timeoutMs) : undefined;
  const input: Input = prompt;
  const streamed = await thread.runStreamed(input, { signal });

  let finalText = "";
  let usage: {
    input_tokens: number;
    cached_input_tokens: number;
    output_tokens: number;
    reasoning_output_tokens: number;
  } | null = null;

  for await (const event of streamed.events) {
    if (event.type === "item.completed" && event.item.type === "agent_message") {
      finalText = event.item.text;
    } else if (event.type === "turn.completed") {
      usage = event.usage;
    } else if (event.type === "turn.failed") {
      throw new HarnessError(event.error.message);
    } else if (event.type === "error") {
      throw new HarnessError(event.message);
    }
  }

  if (logger) {
    logger.logCommand("codex-sdk", ["thread.runStreamed"], {
      stdout: finalText,
      stderr: "",
      exitCode: 0,
    });
  }

  return {
    text: finalText,
    sessionId: thread.id ?? undefined,
    metadata: usage
      ? {
          inputTokens: usage.input_tokens + usage.cached_input_tokens,
          outputTokens: usage.output_tokens,
          cacheReadInputTokens: usage.cached_input_tokens,
        }
      : undefined,
  } satisfies RunnerResponse;
}
