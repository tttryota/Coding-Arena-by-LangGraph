import {
  createRunner,
  EXECUTION_CAPABILITY,
  type ExecutableRunner,
  type ExecutionCapability,
  type ExecutionProviderDefinition,
  type ExecutionService,
} from "./runner.ts";
import type { FlowMode, FlowStep } from "../../shared/steps.ts";
import { FLOW_STEP, LIGHT_SKIP_STEPS } from "../../shared/steps.ts";
import type { HarnessConfig, ResolvedProfileConfig, ResolvedProviderConfig } from "../config.ts";
import { createClaudeExecutionService, CLAUDE_SUPPORTED_CAPABILITIES } from "./claude-runner.ts";
import { createCodexExecutionService, CODEX_SUPPORTED_CAPABILITIES } from "./codex-runner.ts";
import { createGenericExecutionService } from "./generic-runner.ts";
import { HarnessError } from "../../shared/types.ts";
import type { HarnessLogger } from "../logging/logger.ts";
import { EVENT } from "../../shared/types.ts";

export type ProviderRegistry = {
  getRunner(step: FlowStep): ExecutableRunner;
  getRunnerByName(name: string): ExecutableRunner;
  isStepSkipped(step: FlowStep): boolean;
  getFlowMode(): FlowMode;
  getStepMapping(): Record<string, string>;
  getConfig(): HarnessConfig;
};

export type RunnerRegistry = ProviderRegistry;

export function createRunnerRegistry(
  config: HarnessConfig,
  projectRoot: string,
  activeProfile?: ResolvedProfileConfig,
  overrides?: Partial<Record<FlowStep, string>>,
): ProviderRegistry {
  const providers = new Map<string, ExecutionProviderDefinition>();

  for (const [name, providerConfig] of Object.entries(config.providers)) {
    const service = createExecutionService(name, providerConfig, projectRoot);
    validateProviderDefinition(name, providerConfig, service);
    providers.set(name, {
      name,
      policy: providerConfig.capabilityPolicy,
      service,
    });
  }

  const stepMapping: Record<string, string> = resolveStepMapping(config, activeProfile, overrides);

  function wrap(definition: ExecutionProviderDefinition, step?: FlowStep): ExecutableRunner {
    const runner = createRunner(definition.service, definition.policy);
    async function execute(
      request: import("./runner.ts").ExecutionRequest,
      logger?: HarnessLogger,
    ) {
      const response = await runner.execute(request, logger);
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
    }

    return {
      name: runner.name,
      capabilities: runner.capabilities,
      run: execute,
      execute,
    };
  }

  function resolveDefinition(name: string): ExecutionProviderDefinition {
    const definition = providers.get(name);
    if (!definition) throw new HarnessError(`Provider not found: ${name}`);
    return definition;
  }

  return {
    getRunner(step: FlowStep): ExecutableRunner {
      const providerName = stepMapping[step];
      if (!providerName) throw new HarnessError(`No provider assigned for step: ${step}`);
      return wrap(resolveDefinition(providerName), step);
    },
    getRunnerByName(name: string): ExecutableRunner {
      return wrap(resolveDefinition(name));
    },
    isStepSkipped(step: FlowStep): boolean {
      return config.flow === "light" && LIGHT_SKIP_STEPS.has(step);
    },
    getFlowMode: () => config.flow,
    getStepMapping: () => ({ ...stepMapping }),
    getConfig: () => config,
  };
}

function resolveStepMapping(
  config: HarnessConfig,
  activeProfile: ResolvedProfileConfig | undefined,
  overrides?: Partial<Record<FlowStep, string>>,
): Record<string, string> {
  const merged: Record<string, string> = {
    ...config.steps,
  } as Record<string, string>;

  const profileProviders = activeProfile?.stepProviders;
  if (profileProviders?.defaultProvider) {
    for (const step of Object.values(FLOW_STEP)) {
      merged[step] = profileProviders.defaultProvider;
    }
  }
  if (profileProviders?.stepOverrides) {
    for (const [step, providerName] of Object.entries(profileProviders.stepOverrides)) {
      merged[step] = providerName;
    }
  }
  if (overrides) {
    for (const [step, providerName] of Object.entries(overrides)) {
      if (providerName) merged[step] = providerName;
    }
  }

  return merged;
}

function createExecutionService(
  name: string,
  providerConfig: ResolvedProviderConfig,
  projectRoot: string,
): ExecutionService {
  switch (providerConfig.type) {
    case "claude":
      return createClaudeExecutionService({
        name,
        timeoutMs: providerConfig.timeoutMs,
        model: providerConfig.model,
      });
    case "codex":
      return createCodexExecutionService({
        name,
        timeoutMs: providerConfig.timeoutMs,
        sandbox: providerConfig.sandbox,
        heartbeatMs: providerConfig.heartbeatMs,
        stallTimeoutMs: providerConfig.stallTimeoutMs,
        projectRoot,
      });
    case "generic":
      return createGenericExecutionService({
        name,
        command: providerConfig.command,
        args: providerConfig.args,
        promptFlag: providerConfig.promptFlag,
        timeoutMs: providerConfig.timeoutMs,
      });
  }
}

function validateProviderDefinition(
  name: string,
  providerConfig: ResolvedProviderConfig,
  service: ExecutionService,
): void {
  const nativeCapabilities = service.capabilities;
  for (const capability of providerConfig.capabilities) {
    if (!nativeCapabilities.has(capability)) {
      throw new HarnessError(
        `Provider "${name}" declares native capability "${capability}", but transport "${providerConfig.type}" does not support it.`,
      );
    }
  }

  for (const [capability, mode] of Object.entries(providerConfig.capabilityPolicy)) {
    if (mode === "native" && !nativeCapabilities.has(capability as ExecutionCapability)) {
      throw new HarnessError(
        `Provider "${name}" sets capability policy "${capability}=native", but transport "${providerConfig.type}" does not support it.`,
      );
    }
    if (
      capability === EXECUTION_CAPABILITY.SESSION_RESUME &&
      mode === "degrade_to_prompt"
    ) {
      throw new HarnessError(
        `Provider "${name}" cannot degrade "${EXECUTION_CAPABILITY.SESSION_RESUME}" to prompt.`,
      );
    }
  }
}

export const PROVIDER_NATIVE_CAPABILITIES = {
  claude: CLAUDE_SUPPORTED_CAPABILITIES,
  codex: CODEX_SUPPORTED_CAPABILITIES,
  generic: new Set<ExecutionCapability>(),
} as const;
