import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { stringify as stringifyYaml } from "yaml";
import type { Boundary } from "../boundary.ts";
import type { RunnerRegistry } from "../runner-registry.ts";
import type { ResolvedProfileConfig } from "../config.ts";
import { loadTemplate, renderTemplate } from "../templates.ts";
import { applyStepContext } from "../step-context.ts";
import { FLOW_STEP } from "../steps.ts";
import type { BrowserVerificationResult, ReviewIssue, TaskPlan } from "../types.ts";
import { browserIssuesFromResult, parseBrowserVerificationResult } from "../domain/browser-verification.ts";

const DEFAULT_TIMEOUT_MS = 10 * 60 * 1000;

export class PageBrowserService {
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

  async runVerification(
    plan: TaskPlan,
    targetFiles: string[],
  ): Promise<BrowserVerificationResult> {
    const root = this.boundary.getProjectRoot();
    const spec = readFileSync(resolve(root, plan.specPath), "utf-8");
    const config = this.registry.getConfig();
    const template = loadTemplate("review-page-browser", root, config.templates);
    const prompt = renderTemplate(template, {
      spec,
      browserScenarios: stringifyYaml(plan.browserScenarios),
      fileContents: this.renderFiles(targetFiles),
    });

    const runner = this.registry.getRunner(FLOW_STEP.PAGE_BROWSER_VERIFY);
    const response = await runner.run(
      applyStepContext(
        {
          prompt,
          cwd: root,
          timeoutMs: DEFAULT_TIMEOUT_MS,
        },
        config,
        this.profile,
        FLOW_STEP.PAGE_BROWSER_VERIFY,
        root,
        runner.name,
      ),
      undefined,
    );

    return parseBrowserVerificationResult(response.text);
  }

  issuesFromResult(result: BrowserVerificationResult): ReviewIssue[] {
    return browserIssuesFromResult(result);
  }

  async applyFixes(
    issues: ReviewIssue[],
    scopeTools: string[],
  ): Promise<void> {
    const issueList = issues
      .map((issue, index) => `${index + 1}. [${issue.severity}] ${issue.description}`)
      .join("\n");
    const prompt = `以下の Browser Verification 指摘を修正してください。

## 指摘一覧
${issueList}

## 制約
- 仕様書の UX 要件に合致するよう修正する
- ページの配線、状態遷移、レンダリング不整合の修正を優先する
- 不要なリファクタリングは行わない`;

    const runner = this.registry.getRunner(FLOW_STEP.APPLY_FIXES);
    await runner.run(
      applyStepContext(
        {
          prompt,
          allowedTools: scopeTools,
          cwd: this.boundary.getProjectRoot(),
          timeoutMs: DEFAULT_TIMEOUT_MS,
        },
        this.registry.getConfig(),
        this.profile,
        FLOW_STEP.APPLY_FIXES,
        this.boundary.getProjectRoot(),
        runner.name,
      ),
      undefined,
    );
  }

  private renderFiles(files: string[]): string {
    return files
      .map((file) => {
        const content = readFileSync(file, "utf-8");
        return `### ${file}\n\`\`\`\n${content}\n\`\`\``;
      })
      .join("\n\n");
  }
}
