import type { Runner, RunnerRequest, RunnerResponse } from "./runner.ts";
import { prepareRequest } from "./runner.ts";
import type { FlowStep, FlowMode } from "./steps.ts";
import { LIGHT_SKIP_STEPS } from "./steps.ts";
import type { HarnessConfig } from "./config.ts";
import { createClaudeRunner } from "./claude-runner.ts";
import { createCodexRunner } from "./codex-runner.ts";
import { createGenericRunner } from "./generic-runner.ts";
import { HarnessError } from "./types.ts";
import type { HarnessLogger } from "./logger.ts";
import { EVENT } from "./types.ts";

export type RunnerRegistry = {
  getRunner(step: FlowStep): Runner;
  getRunnerByName(name: string): Runner;
  isStepSkipped(step: FlowStep): boolean;
  getFlowMode(): FlowMode;
  getStepMapping(): Record<string, string>;
  getFallbackRunner(): Runner;
  getConfig(): HarnessConfig;
};

export function createRunnerRegistry(
  config: HarnessConfig,
  projectRoot: string,
  overrides?: Partial<Record<FlowStep, string>>,
): RunnerRegistry {
  const runners = new Map<string, Runner>();

  for (const [name, rc] of Object.entries(config.runners)) {
    switch (rc.type) {
      case "claude":
        runners.set(name, createClaudeRunner({ timeoutMs: rc.timeoutMs }));
        break;
      case "codex":
        runners.set(name, createCodexRunner({
          timeoutMs: rc.timeoutMs, sandbox: rc.sandbox, projectRoot,
        }));
        break;
      case "generic":
        runners.set(name, createGenericRunner({
          name, command: rc.command, args: rc.args,
          promptFlag: rc.promptFlag, timeoutMs: rc.timeoutMs,
        }));
        break;
    }
  }

  const stepMapping: Record<string, string> = {
    ...config.steps, ...overrides,
  } as Record<string, string>;

  function wrapRunner(runner: Runner, step?: FlowStep): Runner {
    return {
      name: runner.name,
      capabilities: runner.capabilities,
      async run(request: RunnerRequest, logger?: HarnessLogger): Promise<RunnerResponse> {
        const response = await runner.run(prepareRequest(runner, request), logger);
        if (logger && response.metadata && step) {
          logger.log(EVENT.RUNNER_USAGE, {
            step,
            runner: runner.name,
            inputTokens: response.metadata.inputTokens ?? null,
            outputTokens: response.metadata.outputTokens ?? null,
            cacheCreationInputTokens: response.metadata.cacheCreationInputTokens ?? null,
            cacheReadInputTokens: response.metadata.cacheReadInputTokens ?? null,
            costUsd: response.metadata.costUsd ?? null,
          });
        }
        return response;
      },
    };
  }

  function resolveRunner(name: string): Runner {
    const runner = runners.get(name);
    if (!runner) throw new HarnessError(`Runner not found: ${name}`);
    return wrapRunner(runner);
  }

  return {
    getRunner(step: FlowStep): Runner {
      const runnerName = stepMapping[step];
      if (!runnerName) throw new HarnessError(`No runner assigned for step: ${step}`);
      const runner = runners.get(runnerName);
      if (!runner) throw new HarnessError(`Runner not found: ${runnerName}`);
      return wrapRunner(runner, step);
    },
    getRunnerByName(name: string): Runner {
      return resolveRunner(name);
    },
    isStepSkipped(step: FlowStep): boolean {
      return config.flow === "light" && LIGHT_SKIP_STEPS.has(step);
    },
    getFallbackRunner(): Runner {
      return resolveRunner(config.fallbackRunner);
    },
    getFlowMode: () => config.flow,
    getStepMapping: () => ({ ...stepMapping }),
    getConfig: () => config,
  };
}
