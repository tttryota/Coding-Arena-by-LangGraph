import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { stringify as stringifyYaml } from "yaml";
import type { Boundary } from "../boundary.ts";
import type { RunnerRegistry } from "../runner-registry.ts";
import type { ResolvedProfileConfig } from "../config.ts";
import { loadTemplate, renderTemplate } from "../templates.ts";
import { applyStepContext } from "../step-context.ts";
import { FLOW_STEP } from "../steps.ts";
import type { TaskPlan } from "../types.ts";

const DEFAULT_TIMEOUT_MS = 10 * 60 * 1000;

export class PageGenerationService {
  private boundary: Boundary;
  private registry: RunnerRegistry;
  private profile: ResolvedProfileConfig;

  constructor(
    boundary: Boundary,
    registry: RunnerRegistry,
    profile: ResolvedProfileConfig,
  ) {
    this.boundary = boundary;
    this.registry = registry;
    this.profile = profile;
  }

  async generate(plan: TaskPlan, scopeTools: string[]): Promise<void> {
    const root = this.boundary.getProjectRoot();
    const spec = readFileSync(resolve(root, plan.specPath), "utf-8");
    const componentSpec = readFileSync(resolve(root, plan.componentSpecPath ?? ""), "utf-8");
    const config = this.registry.getConfig();
    const template = loadTemplate("page-generate", root, config.templates);
    const prompt = renderTemplate(template, {
      spec,
      componentSpec,
      dependencies: stringifyYaml(
        plan.dependencies.map((dependency) => ({
          name: dependency.name,
          import: dependency.importPath,
        })),
      ),
      figmaSlice: plan.figmaSlice ?? "",
      browserScenarios: stringifyYaml(plan.browserScenarios),
      targetTestCases: plan.targetTestCases.join("\n"),
    });

    const runner = this.registry.getRunner(FLOW_STEP.PAGE_GENERATE);
    await runner.run(
      applyStepContext(
        {
          prompt,
          allowedTools: scopeTools,
          cwd: root,
          timeoutMs: DEFAULT_TIMEOUT_MS,
        },
        config,
        this.profile,
        FLOW_STEP.PAGE_GENERATE,
        root,
        runner.name,
      ),
      undefined,
    );
  }
}
