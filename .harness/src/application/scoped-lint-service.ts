import type { Boundary } from "../boundary.ts";
import type { ResolvedProfileConfig } from "../config.ts";
import { applyStepContext } from "../step-context.ts";
import { FLOW_STEP } from "../steps.ts";
import type { LintViolation } from "../types.ts";
import type { LintGuard } from "../lint-guard.ts";
import type { RunnerRegistry } from "../runner-registry.ts";

type ScopedLintOptions = {
  scopeTools?: string[];
  root?: string;
};

export class ScopedLintService {
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

  async run(
    lintGuard: LintGuard,
    scope: string,
    phase: string,
    options?: ScopedLintOptions,
  ): Promise<void> {
    console.log(`リントチェック中（${phase}）...`);
    const sourceFiles = await this.boundary.findSourceFiles(scope);
    if (sourceFiles.length === 0) return;

    const claudeFix = options?.scopeTools
      ? async (violations: LintViolation[]) => {
          const issueList = violations
            .map((violation) => `${violation.tool}: ${violation.file}:${violation.line} - ${violation.message}`)
            .join("\n");
          const runner = this.registry.getRunner(FLOW_STEP.LINT_FIX);
          await runner.run(
            applyStepContext(
              {
                prompt: `以下のリンター違反を修正してください。自動修正できなかった違反です。

## 違反一覧
${issueList}

## 制約
- 指摘された違反のみ修正する
- 既存のロジックや振る舞いを変更しない`,
                allowedTools: options.scopeTools,
                cwd: options.root,
              },
              this.registry.getConfig(),
              this.profile,
              FLOW_STEP.LINT_FIX,
              this.boundary.getProjectRoot(),
              runner.name,
            ),
            undefined,
          );
        }
      : undefined;

    await lintGuard.check(sourceFiles, {
      claudeFix,
    });
  }
}
