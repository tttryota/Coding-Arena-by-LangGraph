import type { HarnessLogger } from "../../infrastructure/logging/logger.ts";
import type { ResolvedProfileConfig } from "../../infrastructure/config.ts";
import type { RunnerRegistry } from "../../infrastructure/runners/runner-registry.ts";
import type { FlowStep } from "../../shared/steps.ts";
import { FLOW_STEP } from "../../shared/steps.ts";
import { EVENT } from "../../shared/types.ts";
import { applyStepContext } from "../../shared/step-context.ts";

const DEFAULT_TIMEOUT_MS = 10 * 60 * 1000;

type StepExecutionRequest = {
  prompt: string;
  allowedTools?: string[];
  appendSystemPrompt?: string;
  cwd?: string;
  timeoutMs?: number;
};

export class ReviewStepExecutor {
  private static readonly STALL_FALLBACK_STEPS = new Set<FlowStep>([
    FLOW_STEP.TEST_SELF_QUALITY,
    FLOW_STEP.TEST_EXTERNAL_REVIEW,
    FLOW_STEP.IMPL_SELF_CRITERIA,
    FLOW_STEP.IMPL_SELF_QUALITY,
    FLOW_STEP.IMPL_EXTERNAL_REVIEW,
    FLOW_STEP.APPLY_FIXES,
    FLOW_STEP.JUDGMENT_SUMMARY,
    FLOW_STEP.JUDGE_MINOR,
    FLOW_STEP.PAGE_REVIEW_DESIGN,
    FLOW_STEP.PAGE_REVIEW_BEHAVIOR,
    FLOW_STEP.PAGE_REVIEW_CODE,
    FLOW_STEP.COMPONENT_SELF_REVIEW,
  ]);

  private logger: HarnessLogger;
  private projectRoot: string;
  private registry: RunnerRegistry;
  private profile?: ResolvedProfileConfig;

  constructor(
    logger: HarnessLogger,
    projectRoot: string,
    registry: RunnerRegistry,
    profile?: ResolvedProfileConfig,
  ) {
    this.logger = logger;
    this.projectRoot = projectRoot;
    this.registry = registry;
    this.profile = profile;
  }

  async execute(step: FlowStep, request: StepExecutionRequest): Promise<{ text: string }> {
    const primaryRunner = this.registry.getRunner(step);
    const config = this.registry.getConfig();

    try {
      return await primaryRunner.run(
        applyStepContext(
          {
            prompt: request.prompt,
            allowedTools: request.allowedTools,
            appendSystemPrompt: request.appendSystemPrompt,
            cwd: request.cwd,
            timeoutMs: request.timeoutMs ?? DEFAULT_TIMEOUT_MS,
          },
          config,
          this.profile,
          step,
          this.projectRoot,
          primaryRunner.name,
        ),
        this.logger,
      );
    } catch (error: unknown) {
      const fallbackRunner = this.resolveStallFallbackRunner(step, primaryRunner.name);
      if (!fallbackRunner || !isCodexStallError(error)) {
        throw error;
      }
      const message = error instanceof Error ? error.message : String(error);
      this.logger.log(EVENT.FALLBACK_REVIEW, {
        step,
        reason: "codex_stall_timeout",
        primaryRunner: primaryRunner.name,
        fallbackRunner: fallbackRunner.name,
        message,
      });
      return fallbackRunner.run(
        applyStepContext(
          {
            prompt: request.prompt,
            allowedTools: request.allowedTools,
            appendSystemPrompt: request.appendSystemPrompt,
            cwd: request.cwd,
            timeoutMs: request.timeoutMs ?? DEFAULT_TIMEOUT_MS,
          },
          config,
          this.profile,
          step,
          this.projectRoot,
          fallbackRunner.name,
        ),
        this.logger,
      );
    }
  }

  private resolveStallFallbackRunner(step: FlowStep, primaryRunnerName: string) {
    if (!ReviewStepExecutor.STALL_FALLBACK_STEPS.has(step)) return null;
    const providers = this.registry.getConfig().providers;
    const primaryProvider = providers[primaryRunnerName];
    if (!primaryProvider || primaryProvider.type !== "codex") return null;

    for (const candidate of ["claude_opus", "claude"]) {
      const provider = providers[candidate];
      if (provider?.type === "claude") {
        return this.registry.getRunnerByName(candidate);
      }
    }
    return null;
  }
}

function isCodexStallError(error: unknown): boolean {
  const message = error instanceof Error ? error.message : String(error);
  return /codex sdk run failed: codex turn stalled/i.test(message)
    || /codex turn stalled/i.test(message)
    || /stall_timeout/i.test(message);
}
