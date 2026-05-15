import type { ExecutionService, ExecutionResult } from "./runner.ts";
import { spawnWithStdin } from "../process/spawn.ts";
import { HarnessError } from "../../shared/types.ts";

export type GenericProviderConfig = {
  name: string;
  command: string;
  args: string[];
  promptFlag?: string;
  timeoutMs?: number;
};

export function createGenericExecutionService(
  config: GenericProviderConfig,
): ExecutionService {
  return {
    name: config.name,
    capabilities: new Set(),
    async execute(request, logger) {
      if (request.appendSystemPrompt) {
        throw new HarnessError(
          `${config.name} service received appendSystemPrompt after policy normalization`,
        );
      }
      if (request.allowedTools) {
        throw new HarnessError(
          `${config.name} service received allowedTools after policy normalization`,
        );
      }
      if (request.agent) {
        throw new HarnessError(
          `${config.name} service received agent after policy normalization`,
        );
      }
      if (request.mcpConfigs) {
        throw new HarnessError(
          `${config.name} service received mcpConfigs after policy normalization`,
        );
      }

      const args = [...config.args];
      let stdinData: string;

      if (config.promptFlag) {
        args.push(config.promptFlag, request.prompt);
        stdinData = "";
      } else {
        stdinData = request.prompt;
      }

      const result = await spawnWithStdin(
        config.command,
        args,
        stdinData,
        request.cwd,
        request.timeoutMs ?? config.timeoutMs,
      );

      if (logger) logger.logCommand(config.name, args, result);

      if (result.exitCode !== 0) {
        throw new HarnessError(
          `${config.name} failed (exit ${result.exitCode}): ${result.stderr}`,
        );
      }

      return { text: result.stdout } satisfies ExecutionResult;
    },
  };
}
