import { CodexConversationService } from "./codex-app-server/service.ts";
import { StdioCodexAppServerTransport } from "./codex-app-server/transport.ts";
import { RUNNER_CAPABILITY } from "./runner.ts";
import type { Runner, RunnerResponse } from "./runner.ts";

export function createCodexRunner(defaults?: {
  timeoutMs?: number;
  sandbox?: string;
  projectRoot?: string;
  model?: string;
  approvalPolicy?: "untrusted" | "on-failure" | "on-request" | "never";
  summary?: "auto" | "brief" | "detailed";
  effort?: "minimal" | "low" | "medium" | "high";
  personality?: "default" | "strict" | "balanced";
}): Runner {
  const sandbox = normalizeSandbox(defaults?.sandbox);

  return {
    name: "codex",
    capabilities: new Set([
      RUNNER_CAPABILITY.SESSION_RESUME,
      RUNNER_CAPABILITY.SYSTEM_PROMPT,
      RUNNER_CAPABILITY.REVIEW_API,
    ]),
    async run(request, logger) {
      const transport = new StdioCodexAppServerTransport({
        cwd: defaults?.projectRoot,
        logger,
      });
      const service = new CodexConversationService(transport);
      try {
        return await service.runTurn(
          {
            ...request,
            timeoutMs: request.timeoutMs ?? defaults?.timeoutMs,
            model: request.model ?? defaults?.model,
            approvalPolicy: request.approvalPolicy ?? defaults?.approvalPolicy,
            summary: request.summary ?? defaults?.summary,
            effort: request.effort ?? defaults?.effort,
            personality: request.personality ?? defaults?.personality,
            sandboxPolicy: request.sandboxPolicy ?? sandbox,
          },
          {
            cwd: defaults?.projectRoot,
            sandbox,
            model: defaults?.model,
            approvalPolicy: defaults?.approvalPolicy,
            personality: defaults?.personality,
          },
        );
      } finally {
        await transport.close();
      }
    },
    async review(request, logger) {
      const transport = new StdioCodexAppServerTransport({
        cwd: defaults?.projectRoot,
        logger,
      });
      const service = new CodexConversationService(transport);
      try {
        return await service.runReview(
          {
            ...request,
            timeoutMs: request.timeoutMs ?? defaults?.timeoutMs,
          },
          {
            cwd: defaults?.projectRoot,
            sandbox,
            model: defaults?.model,
            approvalPolicy: defaults?.approvalPolicy,
            personality: defaults?.personality,
          },
        );
      } finally {
        await transport.close();
      }
    },
  };
}

function normalizeSandbox(
  sandbox: string | undefined,
): "read-only" | "workspace-write" | "danger-full-access" | undefined {
  if (!sandbox) return undefined;
  if (sandbox === "read-only" || sandbox === "workspace-write" || sandbox === "danger-full-access") {
    return sandbox;
  }
  throw new Error(`Unsupported codex sandbox mode: ${sandbox}`);
}
