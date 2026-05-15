import type { ResolvedProfileConfig } from "../../infrastructure/config.ts";
import { ImplArtifactsPolicy } from "../../domain/policies/impl-artifacts.ts";
import type { ImplFlowRuntime } from "../runtime/impl-flow-runtime.ts";
import type { RunnerRegistry } from "../../infrastructure/runners/runner-registry.ts";
import { loadTemplate, renderTemplate } from "../../infrastructure/templates.ts";
import { applyStepContext } from "../../shared/step-context.ts";
import { FLOW_STEP } from "../../shared/steps.ts";
import { EVENT } from "../../shared/types.ts";
import type { TaskPlan } from "../../shared/types.ts";
import type { TestAdapter } from "../../shared/tool-adapter.ts";

const DEFAULT_TIMEOUT_MS = 10 * 60 * 1000;

export class ImplGenerationService {
  private registry: RunnerRegistry;
  private profile: ResolvedProfileConfig;
  private testAdapter: TestAdapter;
  private artifacts: ImplArtifactsPolicy;

  constructor(
    registry: RunnerRegistry,
    profile: ResolvedProfileConfig,
    testAdapter: TestAdapter,
    artifacts: ImplArtifactsPolicy,
  ) {
    this.registry = registry;
    this.profile = profile;
    this.testAdapter = testAdapter;
    this.artifacts = artifacts;
  }

  async generateTests(
    plan: TaskPlan,
    runtime: ImplFlowRuntime,
  ): Promise<string> {
    const config = this.registry.getConfig();
    const template = loadTemplate("test-generate", runtime.root, config.templates);
    const prompt = renderTemplate(template, {
      testCases: plan.targetTestCases.join("\n"),
      spec: runtime.spec,
      frameworkName: this.testAdapter.frameworkName,
      mswInstructions: this.artifacts.buildMswInstructions(plan, "test"),
      artifactInstructions: this.artifacts.buildArtifactInstructions(plan, "test"),
      targetTestFile: runtime.targetTestFile,
      targetImplementationFile: runtime.targetImplementationFile,
    });

    this.logPromptPrepared(runtime, FLOW_STEP.TEST_GENERATE, prompt, {
      appendSystemPrompt: runtime.generationSystemPrompt,
      allowedTools: runtime.testGenerateTools,
      primaryTargetFile: runtime.targetTestFile,
    });

    const runner = this.registry.getRunner(FLOW_STEP.TEST_GENERATE);
    const result = await runner.run(
      applyStepContext(
        {
          prompt,
          allowedTools: runtime.testGenerateTools,
          appendSystemPrompt: runtime.generationSystemPrompt,
          cwd: runtime.root,
          timeoutMs: DEFAULT_TIMEOUT_MS,
          observability: {
            step: FLOW_STEP.TEST_GENERATE,
            benchmarkMode: plan.benchmarkMode,
            primaryTargetFile: runtime.targetTestFile,
            relatedFiles: [runtime.targetImplementationFile],
          },
        },
        config,
        this.profile,
        FLOW_STEP.TEST_GENERATE,
        runtime.root,
        runner.name,
      ),
      runtime.logger,
    );

    return result.sessionId ?? "";
  }

  async generateImplementation(
    plan: TaskPlan,
    runtime: ImplFlowRuntime,
    lastFailureOutput: string,
    attempt: number,
    sessionId: string,
  ): Promise<string> {
    const config = this.registry.getConfig();
    const template = attempt === 1
      ? loadTemplate("impl-generate", runtime.root, config.templates)
      : loadTemplate("impl-retry", runtime.root, config.templates);
    const prompt = renderTemplate(template, {
      testOutput: lastFailureOutput,
      spec: runtime.spec,
      mswInstructions: this.artifacts.buildMswInstructions(plan, "impl"),
      artifactInstructions: this.artifacts.buildArtifactInstructions(plan, "impl"),
      targetTestFile: runtime.targetTestFile,
      targetImplementationFile: runtime.targetImplementationFile,
    });

    const runner = this.registry.getRunner(FLOW_STEP.IMPL_GENERATE);
    const result = await runner.run(
      applyStepContext(
        {
          prompt,
          allowedTools: runtime.scopeTools,
          appendSystemPrompt: runtime.generationSystemPrompt,
          sessionId,
          cwd: runtime.root,
          timeoutMs: DEFAULT_TIMEOUT_MS,
        },
        config,
        this.profile,
        FLOW_STEP.IMPL_GENERATE,
        runtime.root,
        runner.name,
      ),
      runtime.logger,
    );

    return result.sessionId ?? sessionId;
  }

  countTestIntents(fileContents: string): number {
    return this.artifacts.countTestIntents(fileContents);
  }

  private logPromptPrepared(
    runtime: ImplFlowRuntime,
    step: string,
    prompt: string,
    options?: {
      appendSystemPrompt?: string;
      allowedTools?: string[];
      primaryTargetFile?: string;
    },
  ): void {
    runtime.logger.log(EVENT.PROMPT_PREPARED, {
      step,
      promptChars: prompt.length,
      promptBytes: Buffer.byteLength(prompt, "utf-8"),
      appendSystemPromptChars: options?.appendSystemPrompt?.length ?? 0,
      appendSystemPromptBytes: Buffer.byteLength(options?.appendSystemPrompt ?? "", "utf-8"),
      allowedToolCount: options?.allowedTools?.length ?? 0,
      primaryTargetFile: options?.primaryTargetFile ?? null,
    });
  }
}
