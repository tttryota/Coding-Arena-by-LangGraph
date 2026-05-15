import { readFileSync } from "node:fs";
import type { HarnessLogger } from "./logger.ts";
import type { LintGuard } from "./lint-guard.ts";
import type { RunnerRegistry } from "./runner-registry.ts";
import type { ResolvedProfileConfig } from "./config.ts";
import type { FlowStep } from "./steps.ts";
import { FLOW_STEP } from "./steps.ts";
import { DriftError, HarnessError, RunnerRateLimitError, ESCALATION_LEVEL, EVENT } from "./types.ts";
import type { ReviewIssue, ReviewResult, ReviewRecord } from "./types.ts";
import { loadTemplate, renderTemplate } from "./templates.ts";
import { applyStepContext } from "./step-context.ts";

const MAX_REVIEW_CYCLES = 5;
const DEFAULT_TIMEOUT_MS = 10 * 60 * 1000;

type ReviewParams = {
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

type PageReviewParams = ReviewParams & {
  componentSpecPath: string;
  figmaSlice: string;
  dependenciesText: string;
  browserScenariosText: string;
};

export class ReviewOrchestrator {
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
  private lintGuard: LintGuard;
  private projectRoot: string;
  private registry: RunnerRegistry;
  private profile?: ResolvedProfileConfig;
  private records: ReviewRecord[] = [];

  constructor(
    logger: HarnessLogger,
    lintGuard: LintGuard,
    projectRoot: string,
    registry: RunnerRegistry,
    profile?: ResolvedProfileConfig,
  ) {
    this.logger = logger;
    this.lintGuard = lintGuard;
    this.projectRoot = projectRoot;
    this.registry = registry;
    this.profile = profile;
  }

  getRecords(): ReviewRecord[] {
    return [...this.records];
  }

  restoreRecords(records: ReviewRecord[]): void {
    this.records = [...records];
  }

  async runReview(params: ReviewParams): Promise<ReviewResult[]> {
    // テストレビューは records をリセット、実装レビューは追記
    if (params.reviewMode === "test") {
      this.records = [];
    }
    const results: ReviewResult[] = [];

    if (params.reviewMode === "test") {
      return this.runTestReview(params, results);
    }
    return this.runImplementationReview(params, results);
  }

  async runPageReview(params: PageReviewParams): Promise<ReviewResult[]> {
    const results: ReviewResult[] = [];
    let minorOnlyCycles = 0;

    this.logger.log(EVENT.REVIEW_START, { mode: "page-3-step" });

    for (let cycle = 0; cycle < MAX_REVIEW_CYCLES; cycle++) {
      const diffBefore = params.getFileDiff
        ? await params.getFileDiff(params.targetFiles)
        : "";

      const cycleResults = [
        await this.pageDesignReview(
          params.targetFiles,
          params.specPath,
          params.componentSpecPath,
          params.dependenciesText,
          params.figmaSlice,
        ),
        await this.pageBehaviorReview(
          params.targetFiles,
          params.specPath,
          params.browserScenariosText,
        ),
        await this.pageCodeReview(
          params.targetFiles,
          params.criteriaPaths,
        ),
      ];
      results.push(...cycleResults);

      const combinedIssues = cycleResults.flatMap((result) => result.issues);
      if (combinedIssues.length === 0) {
        this.records.push({
          step: "page_review",
          cycle: cycle + 1,
          reviewer: "page_review",
          findings: [],
          decision: "lgtm",
          diffBefore,
          diffAfter: "",
          judgmentSummary: "指摘なし",
        });
        return results;
      }

      const hasParseFailure = combinedIssues.some(
        (issue) => issue.file === "" && issue.severity === "critical",
      );
      if (hasParseFailure) {
        this.records.push({
          step: "page_review",
          cycle: cycle + 1,
          reviewer: "page_review",
          findings: combinedIssues,
          decision: "escalated",
          diffBefore,
          diffAfter: "",
          judgmentSummary: "ページレビュー結果のパースに失敗。人間の確認が必要。",
        });
        throw new DriftError(
          ESCALATION_LEVEL.LEVEL_3,
          "page_review_parse_failure",
          "ページレビュー結果のパースに失敗しました。人間の確認が必要です。",
        );
      }

      const hasCriticalOrMajor = combinedIssues.some(
        (issue) => issue.severity === "critical" || issue.severity === "major",
      );

      if (!hasCriticalOrMajor) {
        minorOnlyCycles++;
        if (minorOnlyCycles >= 2) {
          const verdict = await this.judgeMinorAcceptance(
            combinedIssues,
            diffBefore,
            params.specPath,
          );
          if (verdict.safe) {
            this.records.push({
              step: "page_review",
              cycle: cycle + 1,
              reviewer: "page_review",
              findings: combinedIssues,
              decision: "accepted",
              diffBefore,
              diffAfter: "",
              judgmentSummary: verdict.reason,
            });
            return results;
          }
        }
      } else {
        minorOnlyCycles = 0;
      }

      await this.applyFixes(combinedIssues, params, diffBefore);
      const diffAfter = params.getFileDiff
        ? await params.getFileDiff(params.targetFiles)
        : "";
      const judgmentSummary = await this.generateJudgmentSummary(combinedIssues, diffBefore, diffAfter);
      this.records.push({
        step: "page_review",
        cycle: cycle + 1,
        reviewer: "page_review",
        findings: combinedIssues,
        decision: "fixed",
        diffBefore,
        diffAfter,
        judgmentSummary,
      });
    }

    throw new DriftError(
      ESCALATION_LEVEL.LEVEL_1,
      "page_review_cycle",
      `ページレビューが ${MAX_REVIEW_CYCLES} サイクルで収束しませんでした`,
    );
  }

  async runComponentReview(
    targetFiles: string[],
    criteriaPaths: string[],
  ): Promise<ReviewResult> {
    const fileContents = this.readFiles(targetFiles);
    const criteria = criteriaPaths.map((p) => readFileSync(p, "utf-8")).join("\n\n");
    const config = this.registry.getConfig();
    const template = loadTemplate("review-impl-criteria", this.projectRoot, config.templates);
    const responseFormat = loadTemplate("review-response-format", this.projectRoot, config.templates);
    const prompt = renderTemplate(template, { fileContents, responseFormat });
    return this.executeReview(
      FLOW_STEP.COMPONENT_SELF_REVIEW,
      prompt,
      "component_self_review",
      { appendSystemPrompt: criteria },
    );
  }

  private async runTestReview(
    params: ReviewParams,
    results: ReviewResult[],
  ): Promise<ReviewResult[]> {
    this.logger.log(EVENT.REVIEW_START, { mode: "test-2-step" });

    // Step 1: テスト品質チェック（テストケース文書との整合性）
    const step1Result = await this.reviewStep(
      () => this.selfReviewTestQuality(
        params.targetFiles, params.specPath, params.testCasesPath ?? "",
      ),
      params,
    );
    results.push(step1Result);

    // Step 2: 外部レビュー（テストデータの妥当性）
    if (this.registry.isStepSkipped(FLOW_STEP.TEST_EXTERNAL_REVIEW)) {
      // light フロー: 外部レビューをスキップ
    } else {
      try {
        const step2Result = await this.reviewStep(
          () => this.codexTestReview(params.targetFiles, params.specPath, params.testCasesPath ?? ""),
          params,
        );
        results.push(step2Result);
      } catch (error: unknown) {
        if (error instanceof RunnerRateLimitError) {
          this.logger.log(EVENT.RUNNER_RATE_LIMITED, {
            fallback: "none",
            runner: error.runnerName,
            step: FLOW_STEP.TEST_EXTERNAL_REVIEW,
          });
          throw error;
        } else {
          throw error;
        }
      }
    }

    return results;
  }

  private async runImplementationReview(
    params: ReviewParams,
    results: ReviewResult[],
  ): Promise<ReviewResult[]> {
    this.logger.log(EVENT.REVIEW_START, {
      mode: this.registry.isStepSkipped(FLOW_STEP.IMPL_EXTERNAL_REVIEW) ? "impl-2-step" : "impl-3-step",
    });

    // Step 1: セルフレビュー（レビュー観点チェック）
    const step1Result = await this.reviewStep(
      () => this.selfReviewCriteria(params.targetFiles, params.criteriaPaths),
      params,
    );
    results.push(step1Result);

    // Step 2: セルフレビュー（品質チェック）
    const step2Result = await this.reviewStep(
      () => this.selfReviewQuality(params.targetFiles, params.specPath),
      params,
    );
    results.push(step2Result);

    // Step 3: 外部レビュー
    if (this.registry.isStepSkipped(FLOW_STEP.IMPL_EXTERNAL_REVIEW)) {
      // light フロー: 外部レビューをスキップ
    } else {
      try {
        const step3Result = await this.reviewStep(
          () => this.codexReview(params.targetFiles, params.specPath),
          params,
        );
        results.push(step3Result);
      } catch (error: unknown) {
        if (error instanceof RunnerRateLimitError) {
          this.logger.log(EVENT.RUNNER_RATE_LIMITED, {
            fallback: "none",
            runner: error.runnerName,
            step: FLOW_STEP.IMPL_EXTERNAL_REVIEW,
          });
          throw error;
        } else {
          throw error;
        }
      }
    }

    // 設計判断を accepted として記録
    if (params.designDecisions) {
      for (const decision of params.designDecisions) {
        this.records.push({
          step: "design_decision",
          cycle: 0,
          reviewer: "plan",
          findings: [],
          decision: "accepted",
          diffBefore: "",
          diffAfter: "",
          judgmentSummary: decision,
        });
      }
    }

    return results;
  }

  private async selfReviewTestQuality(
    targetFiles: string[],
    specPath: string,
    testCasesPath: string,
  ): Promise<ReviewResult> {
    const fileContents = this.readFiles(targetFiles);
    const spec = readFileSync(specPath, "utf-8");
    const testCases = testCasesPath ? readFileSync(testCasesPath, "utf-8") : "";
    const config = this.registry.getConfig();
    const responseFormat = loadTemplate("review-response-format", this.projectRoot, config.templates);
    const template = loadTemplate("review-test-quality", this.projectRoot, config.templates);
    const prompt = renderTemplate(template, { fileContents, testCases, spec, responseFormat });

    this.logger.log(EVENT.SELF_REVIEW, { step: "test_quality" });
    return this.executeReview(FLOW_STEP.TEST_SELF_QUALITY, prompt, "test_self_quality");
  }

  private async selfReviewCriteria(
    targetFiles: string[],
    criteriaPaths: string[],
  ): Promise<ReviewResult> {
    const fileContents = this.readFiles(targetFiles);
    const criteria = criteriaPaths
      .map((p) => readFileSync(p, "utf-8"))
      .join("\n\n");
    const config = this.registry.getConfig();
    const responseFormat = loadTemplate("review-response-format", this.projectRoot, config.templates);
    const template = loadTemplate("review-impl-criteria", this.projectRoot, config.templates);
    const prompt = renderTemplate(template, { fileContents, responseFormat });

    this.logger.log(EVENT.SELF_REVIEW, { step: "criteria" });
    // Pass criteria as appendSystemPrompt option
    return this.executeReview(FLOW_STEP.IMPL_SELF_CRITERIA, prompt, "self_criteria", { appendSystemPrompt: criteria });
  }

  private async selfReviewQuality(
    targetFiles: string[],
    specPath: string,
  ): Promise<ReviewResult> {
    const fileContents = this.readFiles(targetFiles);
    const spec = readFileSync(specPath, "utf-8");
    const config = this.registry.getConfig();
    const responseFormat = loadTemplate("review-response-format", this.projectRoot, config.templates);
    const template = loadTemplate("review-impl-quality", this.projectRoot, config.templates);
    const prompt = renderTemplate(template, { fileContents, spec, responseFormat });

    this.logger.log(EVENT.SELF_REVIEW, { step: "quality" });
    return this.executeReview(FLOW_STEP.IMPL_SELF_QUALITY, prompt, "self_quality");
  }

  private async codexTestReview(
    targetFiles: string[],
    specPath: string,
    testCasesPath: string,
  ): Promise<ReviewResult> {
    const fileContents = this.readFiles(targetFiles);
    const spec = readFileSync(specPath, "utf-8");
    const testCases = testCasesPath ? readFileSync(testCasesPath, "utf-8") : "";
    const config = this.registry.getConfig();
    const responseFormat = loadTemplate("review-response-format", this.projectRoot, config.templates);
    const template = loadTemplate("review-codex-test", this.projectRoot, config.templates);
    const prompt = renderTemplate(template, { fileContents, testCases, spec, responseFormat });

    return this.executeReview(FLOW_STEP.TEST_EXTERNAL_REVIEW, prompt, "test_external");
  }

  private async codexReview(
    targetFiles: string[],
    specPath: string,
  ): Promise<ReviewResult> {
    const fileContents = this.readFiles(targetFiles);
    const spec = readFileSync(specPath, "utf-8");
    const config = this.registry.getConfig();
    const responseFormat = loadTemplate("review-response-format", this.projectRoot, config.templates);
    const template = loadTemplate("review-codex-impl", this.projectRoot, config.templates);
    const prompt = renderTemplate(template, { fileContents, spec, responseFormat });

    return this.executeReview(FLOW_STEP.IMPL_EXTERNAL_REVIEW, prompt, "impl_external");
  }

  private async pageDesignReview(
    targetFiles: string[],
    specPath: string,
    componentSpecPath: string,
    dependenciesText: string,
    figmaSlice: string,
  ): Promise<ReviewResult> {
    const fileContents = this.readFiles(targetFiles);
    const spec = readFileSync(specPath, "utf-8");
    const componentSpec = readFileSync(componentSpecPath, "utf-8");
    const config = this.registry.getConfig();
    const responseFormat = loadTemplate("review-response-format", this.projectRoot, config.templates);
    const template = loadTemplate("review-page-design", this.projectRoot, config.templates);
    const prompt = renderTemplate(template, {
      fileContents,
      spec,
      componentSpec,
      dependencies: dependenciesText,
      figmaSlice,
      responseFormat,
    });

    return this.executeReview(FLOW_STEP.PAGE_REVIEW_DESIGN, prompt, "page_design");
  }

  private async pageBehaviorReview(
    targetFiles: string[],
    specPath: string,
    browserScenariosText: string,
  ): Promise<ReviewResult> {
    const fileContents = this.readFiles(targetFiles);
    const spec = readFileSync(specPath, "utf-8");
    const config = this.registry.getConfig();
    const responseFormat = loadTemplate("review-response-format", this.projectRoot, config.templates);
    const template = loadTemplate("review-page-behavior", this.projectRoot, config.templates);
    const prompt = renderTemplate(template, {
      fileContents,
      spec,
      browserScenarios: browserScenariosText,
      responseFormat,
    });

    return this.executeReview(FLOW_STEP.PAGE_REVIEW_BEHAVIOR, prompt, "page_behavior");
  }

  private async pageCodeReview(
    targetFiles: string[],
    criteriaPaths: string[],
  ): Promise<ReviewResult> {
    const fileContents = this.readFiles(targetFiles);
    const criteria = criteriaPaths
      .map((p) => readFileSync(p, "utf-8"))
      .join("\n\n");
    const config = this.registry.getConfig();
    const responseFormat = loadTemplate("review-response-format", this.projectRoot, config.templates);
    const template = loadTemplate("review-impl-criteria", this.projectRoot, config.templates);
    const prompt = renderTemplate(template, { fileContents, responseFormat });

    return this.executeReview(
      FLOW_STEP.PAGE_REVIEW_CODE,
      prompt,
      "page_code",
      { appendSystemPrompt: criteria },
    );
  }

  private async reviewStep(
    reviewFn: () => Promise<ReviewResult>,
    params: ReviewParams,
  ): Promise<ReviewResult> {
    const MAX_MINOR_ONLY_CYCLES = 2;
    let minorOnlyCycles = 0;

    for (let cycle = 0; cycle < MAX_REVIEW_CYCLES; cycle++) {
      const diffBefore = params.getFileDiff
        ? await params.getFileDiff(params.targetFiles)
        : "";
      const result = await reviewFn();

      if (result.isLgtm) {
        this.records.push({
          step: result.reviewer,
          cycle: cycle + 1,
          reviewer: result.reviewer,
          findings: [],
          decision: "lgtm",
          diffBefore,
          diffAfter: "",
          judgmentSummary: "指摘なし",
        });
        return result;
      }

      // パース失敗等の擬似 issue は自動修正せずエスカレーション
      const hasParseFailure = result.issues.some(
        (i) => i.file === "" && i.severity === "critical",
      );
      if (hasParseFailure) {
        this.records.push({
          step: result.reviewer,
          cycle: cycle + 1,
          reviewer: result.reviewer,
          findings: result.issues,
          decision: "escalated",
          diffBefore,
          diffAfter: "",
          judgmentSummary: "レビュー結果のパースに失敗。人間のエスカレーションが必要。",
        });
        throw new DriftError(
          ESCALATION_LEVEL.LEVEL_3,
          "review_parse_failure",
          `レビュー結果のパースに失敗しました（reviewer: ${result.reviewer}）。人間の確認が必要です。`,
        );
      }

      // minor のみの判定
      const hasCriticalOrMajor = result.issues.some(
        (i) => i.severity === "critical" || i.severity === "major",
      );

      if (!hasCriticalOrMajor) {
        minorOnlyCycles++;
        if (minorOnlyCycles >= MAX_MINOR_ONLY_CYCLES) {
          // 第三者 Claude に許容可否を判断させる
          const verdict = await this.judgeMinorAcceptance(
            result.issues, diffBefore, params.specPath,
          );
          if (verdict.safe) {
            for (const issue of result.issues) {
              this.records.push({
                step: result.reviewer,
                cycle: cycle + 1,
                reviewer: result.reviewer,
                findings: [issue],
                decision: "accepted",
                diffBefore,
                diffAfter: "",
                judgmentSummary: verdict.reason,
              });
            }
            return result;
          }
          // unsafe → 修正を再試行（1回のみ）
          await this.applyFixes(result.issues, params, diffBefore);
          const retryResult = await reviewFn();
          const diffAfterRetry = params.getFileDiff
            ? await params.getFileDiff(params.targetFiles)
            : "";
          if (retryResult.isLgtm) {
            this.records.push({
              step: result.reviewer,
              cycle: cycle + 2,
              reviewer: result.reviewer,
              findings: [],
              decision: "lgtm",
              diffBefore,
              diffAfter: diffAfterRetry,
              judgmentSummary: `第三者判断により修正: ${verdict.reason}`,
            });
            return retryResult;
          }
          // 修正後も残存 → escalated
          this.records.push({
            step: result.reviewer,
            cycle: cycle + 2,
            reviewer: result.reviewer,
            findings: retryResult.issues,
            decision: "escalated",
            diffBefore,
            diffAfter: diffAfterRetry,
            judgmentSummary: `${verdict.reason}（修正後も残存）`,
          });
          return retryResult;
        }
      } else {
        minorOnlyCycles = 0;
      }

      await this.applyFixes(result.issues, params, diffBefore);

      const diffAfter = params.getFileDiff
        ? await params.getFileDiff(params.targetFiles)
        : "";

      // 判断理由を生成
      const judgmentSummary = await this.generateJudgmentSummary(result.issues, diffBefore, diffAfter);

      this.records.push({
        step: result.reviewer,
        cycle: cycle + 1,
        reviewer: result.reviewer,
        findings: result.issues,
        decision: "fixed",
        diffBefore,
        diffAfter,
        judgmentSummary,
      });
    }

    throw new DriftError(
      ESCALATION_LEVEL.LEVEL_1,
      "review_cycle",
      `レビューが ${MAX_REVIEW_CYCLES} サイクルで収束しませんでした`,
    );
  }

  private async applyFixes(
    issues: ReviewIssue[],
    params: ReviewParams,
    diffBefore = "",
  ): Promise<void> {
    const issueList = issues
      .map(
        (i, idx) =>
          `${idx + 1}. [${i.severity}] ${i.file}:${i.line ?? "?"} - ${i.description}`,
      )
      .join("\n");
    const fileContents = this.readFiles(params.targetFiles);
    const spec = readFileSync(params.specPath, "utf-8");
    const testCases = params.testCasesPath ? readFileSync(params.testCasesPath, "utf-8") : "";
    const criteria = params.criteriaPaths.length > 0
      ? params.criteriaPaths.map((p) => readFileSync(p, "utf-8")).join("\n\n")
      : "";

    const hasBugFix = issues.some(
      (i) => i.severity === "critical" || i.severity === "major",
    );
    const constraint = hasBugFix
      ? `- バグ修正の場合は振る舞いの変更を許可する
- 仕様書に記載された振る舞いに合致させること
- 既存テストが壊れた場合はテストも修正する`
      : `- 指摘された箇所のみ修正
- 既存テストを壊さない
- 振る舞いを変えない（リファクタリングのみ）`;

    const sections = [
      "以下のレビュー指摘を修正してください。",
      "## 指摘一覧",
      issueList,
      "## 現在の対象ファイル",
      fileContents,
      "## 仕様書",
      spec,
      testCases ? `## 承認済みテストケース\n${testCases}` : "",
      criteria ? `## レビュー観点\n${criteria}` : "",
      diffBefore ? `## 直前の差分\n${diffBefore}` : "",
      "## 制約",
      constraint,
      "- issue 解消だけでなく、今回触ったファイルの lint/type も通る状態にする",
      "- repo 全体の探索や pytest 実行方法の探索は始めず、対象ファイルの修正に集中する",
      "- 明らかな lint/type 違反を新たに作らない",
    ].filter((section) => section !== "");
    const prompt = sections.join("\n\n");

    await this.executeRun(FLOW_STEP.APPLY_FIXES, prompt, {
      allowedTools: params.scopeAllowedTools,
      cwd: this.projectRoot,
    });

    if (params.rescanFiles) {
      params.targetFiles = await params.rescanFiles();
    }

    if (params.targetFiles.length > 0) {
      await this.lintGuard.check(params.targetFiles, {
        claudeFix: async (violations) => {
          const lintIssueList = violations
            .map((v, idx) => `${idx + 1}. ${v.tool}: ${v.file}:${v.line} - ${v.message}`)
            .join("\n");
          const lintPrompt = [
            "以下の lint/type 違反を修正してください。",
            "## 違反一覧",
            lintIssueList,
            "## 現在の対象ファイル",
            this.readFiles(params.targetFiles),
            "## 制約",
            "- 違反が出ている対象ファイルだけを修正する",
            "- レビュー指摘で直した契約や振る舞いを壊さない",
            "- `try`-`except`-`pass` や例外握り潰しで違反を回避しない",
          ].join("\n\n");
          await this.executeRun(FLOW_STEP.LINT_FIX, lintPrompt, {
            allowedTools: params.scopeAllowedTools,
            cwd: this.projectRoot,
          });
        },
        rescanFiles: params.rescanFiles,
      });
    }
    if (params.reviewMode !== "test" && params.runTests) {
      await params.runTests();
    }
  }

  private parseReviewResult(reviewer: string, output: string): ReviewResult {
    try {
      // コードフェンス（```json ... ```）を除去
      const cleaned = output.replace(/```(?:json)?\s*\n([\s\S]*?)```/g, "$1");

      // JSON.parse を直接試行し、失敗したら正規表現で抽出（非 greedy）
      let parsed: Record<string, unknown>;
      try {
        parsed = JSON.parse(cleaned) as Record<string, unknown>;
      } catch {
        // 非 greedy: "issues" を含む最初の {...} を抽出
        const jsonMatch = /\{[^{}]*"issues"\s*:\s*\[[\s\S]*?\]\s*\}/.exec(cleaned);
        if (!jsonMatch) {
          throw new HarnessError(`レビュー出力からJSONを抽出できませんでした (reviewer: ${reviewer})`);
        }
        parsed = JSON.parse(jsonMatch[0]) as Record<string, unknown>;
      }

      // schema validation: issues が配列であることを確認
      if (!Array.isArray(parsed.issues)) {
        throw new HarnessError(`issues フィールドが配列ではありません (reviewer: ${reviewer})`);
      }

      // 各 issue の最低限の形状を検証
      const validatedIssues: ReviewIssue[] = [];
      let invalidCount = 0;
      for (const item of parsed.issues) {
        if (
          typeof item === "object" && item !== null &&
          typeof (item as Record<string, unknown>).description === "string" &&
          typeof (item as Record<string, unknown>).severity === "string" &&
          typeof (item as Record<string, unknown>).file === "string"
        ) {
          const i = item as Record<string, unknown>;
          validatedIssues.push({
            description: i.description as string,
            severity: (["critical", "major", "minor"].includes(i.severity as string)
              ? i.severity : "major") as "critical" | "major" | "minor",
            file: i.file as string,
            line: typeof i.line === "number" ? i.line : undefined,
          });
        } else {
          invalidCount++;
        }
      }

      // 不正要素がある場合: fail-closed
      if (invalidCount > 0) {
        throw new HarnessError(
          `レビュー出力に ${invalidCount} 件の不正な issue が含まれています (reviewer: ${reviewer})。有効: ${validatedIssues.length} 件`,
        );
      }

      return {
        reviewer,
        issues: validatedIssues,
        isLgtm: validatedIssues.length === 0,
      };
    } catch {
      // fail-closed: パース失敗時は LGTM にしない
      return {
        reviewer,
        issues: [
          {
            description: `レビュー結果のパースに失敗しました。出力を手動確認してください。`,
            severity: "critical",
            file: "",
          },
        ],
        isLgtm: false,
      };
    }
  }

  private async generateJudgmentSummary(
    issues: ReviewIssue[],
    diffBefore: string,
    diffAfter: string,
  ): Promise<string> {
    const issueText = issues
      .map((i) => `[${i.severity}] ${i.file}:${i.line ?? "?"} - ${i.description}`)
      .join("\n");

    try {
      const prompt = `以下のレビュー指摘に対してコード修正が行われました。なぜこの修正が必要だったのか、どういう判断で対応したかを3行以内で日本語で説明してください。

## レビュー指摘
${issueText}

## 修正前のdiff
${diffBefore.slice(0, 2000)}

## 修正後のdiff
${diffAfter.slice(0, 2000)}`;

      return this.executeRun(FLOW_STEP.JUDGMENT_SUMMARY, prompt, { allowedTools: ["Read"] });
    } catch {
      return "（判断理由の生成に失敗しました）";
    }
  }

  private async judgeMinorAcceptance(
    issues: ReviewIssue[],
    diffHistory: string,
    specPath: string,
  ): Promise<{ safe: boolean; reason: string }> {
    const issueText = issues
      .map((i) => `[${i.severity}] ${i.file}:${i.line ?? "?"} - ${i.description}`)
      .join("\n");
    const spec = readFileSync(specPath, "utf-8");

    try {
      const prompt = `あなたは第三者のコードレビュアーです。
以下の minor 指摘について、2回の修正試行後も解消されていません。
この指摘を許容（対応しない）して安全かどうか判断してください。

## 未解消の指摘
${issueText}

## 修正試行の履歴（diff）
${diffHistory.slice(0, 3000)}

## 仕様書
${spec.slice(0, 3000)}

## 判断基準
- 機能の正確性に影響するか
- 保守性に深刻な影響を与えるか
- 仕様書の要件を満たしているか

## 回答形式（厳守）
{"safe": true, "reason": "判断理由"}
または
{"safe": false, "reason": "判断理由"}`;

      const rawResult = await this.executeRun(FLOW_STEP.JUDGE_MINOR, prompt, { allowedTools: ["Read"] });

      const cleaned = rawResult.replace(/```(?:json)?\s*\n([\s\S]*?)```/g, "$1");
      const parsed = JSON.parse(cleaned) as { safe?: boolean; reason?: string };
      return {
        safe: parsed.safe ?? true,
        reason: parsed.reason ?? "（判断理由なし）",
      };
    } catch {
      // フォールバック: 判断失敗時は safe=true（ハーネスを止めない）
      return { safe: true, reason: "（第三者判断の生成に失敗。許容として扱う）" };
    }
  }

  private readFiles(files: string[]): string {
    return files
      .map((f) => {
        const content = readFileSync(f, "utf-8");
        return `### ${f}\n\`\`\`\n${content}\n\`\`\``;
      })
      .join("\n\n");
  }

  private async executeReview(
    step: FlowStep,
    prompt: string,
    reviewer: string,
    options?: {
      allowedTools?: string[];
      appendSystemPrompt?: string;
      timeoutMs?: number;
    },
  ): Promise<ReviewResult> {
    const response = await this.executeStepWithFallback(step, {
      prompt,
      allowedTools: options?.allowedTools ?? ["Read"],
      timeoutMs: options?.timeoutMs ?? DEFAULT_TIMEOUT_MS,
      appendSystemPrompt: options?.appendSystemPrompt,
    });
    return this.parseReviewResult(reviewer, response.text);
  }

  private async executeRun(
    step: FlowStep,
    prompt: string,
    options?: {
      allowedTools?: string[];
      appendSystemPrompt?: string;
      cwd?: string;
      timeoutMs?: number;
    },
  ): Promise<string> {
    const response = await this.executeStepWithFallback(step, {
      prompt,
      allowedTools: options?.allowedTools,
      appendSystemPrompt: options?.appendSystemPrompt,
      cwd: options?.cwd,
      timeoutMs: options?.timeoutMs ?? DEFAULT_TIMEOUT_MS,
    });
    return response.text;
  }

  private async executeStepWithFallback(
    step: FlowStep,
    request: {
      prompt: string;
      allowedTools?: string[];
      appendSystemPrompt?: string;
      cwd?: string;
      timeoutMs?: number;
    },
  ): Promise<{ text: string }> {
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
      if (!fallbackRunner || !this.isCodexStallError(error)) {
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
    if (!ReviewOrchestrator.STALL_FALLBACK_STEPS.has(step)) return null;
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

  private isCodexStallError(error: unknown): boolean {
    const message = error instanceof Error ? error.message : String(error);
    return /codex sdk run failed: codex turn stalled/i.test(message)
      || /codex turn stalled/i.test(message)
      || /stall_timeout/i.test(message);
  }
}
