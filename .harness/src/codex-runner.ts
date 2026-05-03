import type { Runner, RunnerResponse } from "./runner.ts";
import { spawnWithStdin } from "./spawn.ts";
import { HarnessError, RunnerRateLimitError } from "./types.ts";

export function createCodexRunner(defaults?: {
  timeoutMs?: number;
  sandbox?: string;
  projectRoot?: string;
}): Runner {
  return {
    name: "codex",
    capabilities: new Set([]),
    async run(request, logger) {
      const args = ["exec"];
      args.push("--sandbox", defaults?.sandbox ?? "read-only");
      const cwd = request.cwd ?? defaults?.projectRoot;
      if (cwd) args.push("--cd", cwd);
      args.push("-");

      const fullPrompt = request.appendSystemPrompt
        ? `${request.prompt}\n\n---\n${request.appendSystemPrompt}`
        : request.prompt;

      const result = await spawnWithStdin(
        "codex", args, fullPrompt, undefined,
        request.timeoutMs ?? defaults?.timeoutMs,
      );

      if (logger) logger.logCommand("codex", args, result);

      if (result.exitCode !== 0) {
        if (/rate|limit|429/i.test(result.stderr)) {
          throw new RunnerRateLimitError("codex", result.stderr);
        }
        throw new HarnessError(`codex exec failed (exit ${result.exitCode}): ${result.stderr}`);
      }

      return { text: result.stdout } satisfies RunnerResponse;
    },
  };
}
