import type { LintGuard } from "../lint-guard.ts";
import type { FlowStep } from "../steps.ts";
import { FLOW_STEP } from "../steps.ts";
import { parseMinorAcceptanceVerdict } from "../domain/review-output.ts";
import { ReviewCycle } from "../domain/review-cycle.ts";
import type { ReviewPromptFactory } from "./review-prompt-factory.ts";
import type { LintViolation, ReviewIssue, ReviewRecord, ReviewResult } from "../types.ts";
import { DriftError, ESCALATION_LEVEL } from "../types.ts";

const MAX_REVIEW_CYCLES = 5;

export type ReviewCycleParams = {
  targetFiles: string[];
  specPath: string;
  criteriaPaths: string[];
  runTests?: () => Promise<void>;
  rescanFiles?: () => Promise<string[]>;
  scopeAllowedTools: string[];
  getFileDiff?: (files: string[]) => Promise<string>;
  designDecisions?: string[];
  reviewMode: "test" | "implementation";
  testCasesPath?: string;
};

export type PageReviewCycleParams = ReviewCycleParams & {
  componentSpecPath: string;
  figmaSlice: string;
  dependenciesText: string;
  browserScenariosText: string;
};

export type ReviewStepDefinition = {
  step: FlowStep;
  reviewer: string;
  mode: "test" | "implementation" | "page";
  run: () => Promise<ReviewResult>;
};

type ExecuteRun = (
  step: FlowStep,
  prompt: string,
  options?: {
    allowedTools?: string[];
    appendSystemPrompt?: string;
    cwd?: string;
    timeoutMs?: number;
  },
) => Promise<string>;

export class ReviewCycleService {
  private lintGuard: LintGuard;
  private prompts: ReviewPromptFactory;
  private executeRun: ExecuteRun;
  private projectRoot: string;

  constructor(
    lintGuard: LintGuard,
    prompts: ReviewPromptFactory,
    executeRun: ExecuteRun,
    projectRoot: string,
  ) {
    this.lintGuard = lintGuard;
    this.prompts = prompts;
    this.executeRun = executeRun;
    this.projectRoot = projectRoot;
  }

  async runSequentialReview(
    stepDefinitions: ReviewStepDefinition[],
    params: ReviewCycleParams,
    records: ReviewRecord[],
  ): Promise<ReviewResult[]> {
    const results: ReviewResult[] = [];
    for (const definition of stepDefinitions) {
      results.push(await this.runStepCycle(definition, params, records));
    }
    return results;
  }

  async runCompositeReview(
    recordStep: string,
    stepDefinitions: ReviewStepDefinition[],
    params: PageReviewCycleParams,
    records: ReviewRecord[],
  ): Promise<ReviewResult[]> {
    const cycleState = new ReviewCycle();
    const results: ReviewResult[] = [];

    while (!cycleState.shouldEscalate(MAX_REVIEW_CYCLES)) {
      const diffBefore = await this.resolveDiff(params);
      const cycleResults: ReviewResult[] = [];
      for (const definition of stepDefinitions) {
        cycleResults.push(await definition.run());
      }
      results.push(...cycleResults);

      const combinedIssues = cycleResults.flatMap((result) => result.issues);
      cycleState.record({
        issues: combinedIssues,
        isLgtm: combinedIssues.length === 0,
      });

      if (cycleState.isLgtm()) {
        records.push(this.buildRecord(recordStep, cycleState.getCycle(), recordStep, [], "lgtm", diffBefore, "", "指摘なし"));
        return results;
      }

      if (cycleState.hasParseFailure()) {
        records.push(
          this.buildRecord(
            recordStep,
            cycleState.getCycle(),
            recordStep,
            combinedIssues,
            "escalated",
            diffBefore,
            "",
            "ページレビュー結果のパースに失敗。人間の確認が必要。",
          ),
        );
        throw new DriftError(
          ESCALATION_LEVEL.LEVEL_3,
          "page_review_parse_failure",
          "ページレビュー結果のパースに失敗しました。人間の確認が必要です。",
        );
      }

      if (cycleState.shouldJudgeMinorAcceptance()) {
        const verdict = await this.judgeMinorAcceptance(combinedIssues, diffBefore, params.specPath);
        if (verdict.safe) {
          records.push(
            this.buildRecord(recordStep, cycleState.getCycle(), recordStep, combinedIssues, "accepted", diffBefore, "", verdict.reason),
          );
          return results;
        }
      }

      await this.applyFixes(combinedIssues, params, diffBefore);
      const diffAfter = await this.resolveDiff(params);
      const judgmentSummary = await this.generateJudgmentSummary(combinedIssues, diffBefore, diffAfter);
      records.push(
        this.buildRecord(recordStep, cycleState.getCycle(), recordStep, combinedIssues, "fixed", diffBefore, diffAfter, judgmentSummary),
      );
    }

    throw new DriftError(
      ESCALATION_LEVEL.LEVEL_1,
      "page_review_cycle",
      `ページレビューが ${MAX_REVIEW_CYCLES} サイクルで収束しませんでした`,
    );
  }

  private async runStepCycle(
    definition: ReviewStepDefinition,
    params: ReviewCycleParams,
    records: ReviewRecord[],
  ): Promise<ReviewResult> {
    const cycleState = new ReviewCycle();

    while (!cycleState.shouldEscalate(MAX_REVIEW_CYCLES)) {
      const diffBefore = await this.resolveDiff(params);
      const result = await definition.run();
      cycleState.record(result);

      if (cycleState.isLgtm()) {
        records.push(this.buildRecord(result.reviewer, cycleState.getCycle(), result.reviewer, [], "lgtm", diffBefore, "", "指摘なし"));
        return result;
      }

      if (cycleState.hasParseFailure()) {
        records.push(
          this.buildRecord(
            result.reviewer,
            cycleState.getCycle(),
            result.reviewer,
            result.issues,
            "escalated",
            diffBefore,
            "",
            "レビュー結果のパースに失敗。人間のエスカレーションが必要。",
          ),
        );
        throw new DriftError(
          ESCALATION_LEVEL.LEVEL_3,
          "review_parse_failure",
          `レビュー結果のパースに失敗しました（reviewer: ${result.reviewer}）。人間の確認が必要です。`,
        );
      }

      if (cycleState.shouldJudgeMinorAcceptance()) {
        const verdict = await this.judgeMinorAcceptance(result.issues, diffBefore, params.specPath);
        if (verdict.safe) {
          for (const issue of result.issues) {
            records.push(
              this.buildRecord(result.reviewer, cycleState.getCycle(), result.reviewer, [issue], "accepted", diffBefore, "", verdict.reason),
            );
          }
          return result;
        }

        await this.applyFixes(result.issues, params, diffBefore);
        const retryResult = await definition.run();
        cycleState.record(retryResult);
        const diffAfterRetry = await this.resolveDiff(params);

        if (retryResult.isLgtm) {
          records.push(
            this.buildRecord(
              retryResult.reviewer,
              cycleState.getCycle(),
              retryResult.reviewer,
              [],
              "lgtm",
              diffBefore,
              diffAfterRetry,
              `第三者判断により修正: ${verdict.reason}`,
            ),
          );
          return retryResult;
        }

        records.push(
          this.buildRecord(
            retryResult.reviewer,
            cycleState.getCycle(),
            retryResult.reviewer,
            retryResult.issues,
            "escalated",
            diffBefore,
            diffAfterRetry,
            `${verdict.reason}（修正後も残存）`,
          ),
        );
        return retryResult;
      }

      await this.applyFixes(result.issues, params, diffBefore);
      const diffAfter = await this.resolveDiff(params);
      const judgmentSummary = await this.generateJudgmentSummary(result.issues, diffBefore, diffAfter);
      records.push(
        this.buildRecord(result.reviewer, cycleState.getCycle(), result.reviewer, result.issues, "fixed", diffBefore, diffAfter, judgmentSummary),
      );
    }

    throw new DriftError(
      ESCALATION_LEVEL.LEVEL_1,
      "review_cycle",
      `レビューが ${MAX_REVIEW_CYCLES} サイクルで収束しませんでした`,
    );
  }

  private async applyFixes(
    issues: ReviewIssue[],
    params: ReviewCycleParams,
    diffBefore = "",
  ): Promise<void> {
    const prompt = this.prompts.buildApplyFixesPrompt(issues, {
      targetFiles: params.targetFiles,
      specPath: params.specPath,
      testCasesPath: params.testCasesPath,
      criteriaPaths: params.criteriaPaths,
      diffBefore,
    });

    await this.executeRun(FLOW_STEP.APPLY_FIXES, prompt, {
      allowedTools: params.scopeAllowedTools,
      cwd: this.projectRoot,
    });

    if (params.rescanFiles) {
      params.targetFiles = await params.rescanFiles();
    }

    if (params.targetFiles.length > 0) {
      await this.lintGuard.check(params.targetFiles, {
        claudeFix: async (violations) => this.fixLintViolations(violations, params),
        rescanFiles: params.rescanFiles,
      });
    }
    if (params.reviewMode !== "test" && params.runTests) {
      await params.runTests();
    }
  }

  private async fixLintViolations(
    violations: LintViolation[],
    params: ReviewCycleParams,
  ): Promise<void> {
    const lintPrompt = this.prompts.buildLintFixPrompt(violations, params.targetFiles);
    await this.executeRun(FLOW_STEP.LINT_FIX, lintPrompt, {
      allowedTools: params.scopeAllowedTools,
      cwd: this.projectRoot,
    });
  }

  private async generateJudgmentSummary(
    issues: ReviewIssue[],
    diffBefore: string,
    diffAfter: string,
  ): Promise<string> {
    try {
      const prompt = this.prompts.buildJudgmentSummaryPrompt(issues, diffBefore, diffAfter);
      return await this.executeRun(FLOW_STEP.JUDGMENT_SUMMARY, prompt, { allowedTools: ["Read"] });
    } catch {
      return "（判断理由の生成に失敗しました）";
    }
  }

  private async judgeMinorAcceptance(
    issues: ReviewIssue[],
    diffHistory: string,
    specPath: string,
  ): Promise<{ safe: boolean; reason: string }> {
    try {
      const prompt = this.prompts.buildMinorAcceptancePrompt(issues, diffHistory, specPath);
      const rawResult = await this.executeRun(FLOW_STEP.JUDGE_MINOR, prompt, { allowedTools: ["Read"] });
      return parseMinorAcceptanceVerdict(rawResult);
    } catch {
      return { safe: true, reason: "（第三者判断の生成に失敗。許容として扱う）" };
    }
  }

  private async resolveDiff(params: ReviewCycleParams): Promise<string> {
    return params.getFileDiff
      ? await params.getFileDiff(params.targetFiles)
      : "";
  }

  private buildRecord(
    step: string,
    cycle: number,
    reviewer: string,
    findings: ReviewIssue[],
    decision: ReviewRecord["decision"],
    diffBefore: string,
    diffAfter: string,
    judgmentSummary: string,
  ): ReviewRecord {
    return {
      step,
      cycle,
      reviewer,
      findings,
      decision,
      diffBefore,
      diffAfter,
      judgmentSummary,
    };
  }
}
