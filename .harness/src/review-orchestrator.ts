import { readFileSync } from "node:fs";
import { spawn } from "node:child_process";
import type { HarnessLogger } from "./logger.ts";
import type { LintGuard } from "./lint-guard.ts";
import { runClaude } from "./claude-runner.ts";
import { DriftError, HarnessError, ESCALATION_LEVEL, EVENT } from "./types.ts";
import type { ReviewIssue, ReviewResult, ReviewRecord, CommandResult } from "./types.ts";
import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const MAX_REVIEW_CYCLES = 5;
const DEFAULT_TIMEOUT_MS = 10 * 60 * 1000;
const CODEX_TIMEOUT_MS = 20 * 60 * 1000;
const LOCAL_CMD_TIMEOUT_MS = 5 * 60 * 1000;

type ReviewParams = {
  targetFiles: string[];
  specPath: string;
  criteriaPaths: string[];
  testCommand: string[];
  rescanFiles?: () => Promise<string[]>;
  scopeAllowedTools: string[];
  getFileDiff?: (files: string[]) => Promise<string>;
  designDecisions?: string[];
  reviewMode: "test" | "implementation";
  testCasesPath?: string;
};

export class ReviewOrchestrator {
  private logger: HarnessLogger;
  private lintGuard: LintGuard;
  private projectRoot: string;
  private codexAvailable: boolean;
  private records: ReviewRecord[] = [];

  constructor(
    logger: HarnessLogger,
    lintGuard: LintGuard,
    projectRoot: string,
    options?: { codexAvailable?: boolean },
  ) {
    this.logger = logger;
    this.lintGuard = lintGuard;
    this.projectRoot = projectRoot;
    this.codexAvailable = options?.codexAvailable ?? true;
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

    // Step 2: Codex レビュー（テストデータの妥当性）
    if (this.codexAvailable) {
      try {
        const step2Result = await this.reviewStep(
          () => this.codexTestReview(params.targetFiles, params.specPath, params.testCasesPath ?? ""),
          params,
        );
        results.push(step2Result);
      } catch (error: unknown) {
        if (isCodexRateLimit(error)) {
          this.logger.log(EVENT.CODEX_RATE_LIMITED, { fallback: "dual_claude" });
          this.codexAvailable = false;
          const dualResult = await this.runDualStep(params);
          results.push(...dualResult);
        } else {
          throw error;
        }
      }
    } else {
      const dualResult = await this.runDualStep(params);
      results.push(...dualResult);
    }

    return results;
  }

  private async runImplementationReview(
    params: ReviewParams,
    results: ReviewResult[],
  ): Promise<ReviewResult[]> {
    this.logger.log(EVENT.REVIEW_START, {
      mode: this.codexAvailable ? "impl-3-step" : "impl-2-step",
    });

    // Step 1: セルフレビュー（レビュー観点チェック）
    const step1Result = await this.reviewStep(
      () => this.selfReviewCriteria(params.targetFiles, params.criteriaPaths),
      params,
    );
    results.push(step1Result);

    if (this.codexAvailable) {
      // 3ステップフロー
      const step2Result = await this.reviewStep(
        () => this.selfReviewQuality(params.targetFiles, params.specPath),
        params,
      );
      results.push(step2Result);

      try {
        const step3Result = await this.reviewStep(
          () => this.codexReview(params.targetFiles, params.specPath),
          params,
        );
        results.push(step3Result);
      } catch (error: unknown) {
        if (isCodexRateLimit(error)) {
          this.logger.log(EVENT.CODEX_RATE_LIMITED, { fallback: "dual_claude" });
          this.codexAvailable = false;
          const dualResult = await this.runDualStep(params);
          results.push(...dualResult);
        } else {
          throw error;
        }
      }
    } else {
      const dualResult = await this.runDualStep(params);
      results.push(...dualResult);
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

  private async runDualStep(params: ReviewParams): Promise<ReviewResult[]> {
    const results: ReviewResult[] = [];
    let cycle = 0;

    while (cycle < MAX_REVIEW_CYCLES) {
      cycle++;
      const diffBefore = params.getFileDiff
        ? await params.getFileDiff(params.targetFiles)
        : "";

      const [reviewA, reviewB] = await this.dualClaudeReview(
        params.targetFiles,
        params.specPath,
      );

      this.logger.log(EVENT.CLAUDE_REVIEW, {
        agent: "A",
        issues: reviewA.issues.length,
      });
      this.logger.log(EVENT.CLAUDE_REVIEW, {
        agent: "B",
        issues: reviewB.issues.length,
      });

      // パース失敗チェック（両エージェント）
      const hasParseFailure = [...reviewA.issues, ...reviewB.issues].some(
        (i) => i.file === "" && i.severity === "critical",
      );
      if (hasParseFailure) {
        this.records.push({
          step: "dual_claude",
          cycle,
          reviewer: "agent_a+agent_b",
          findings: [...reviewA.issues, ...reviewB.issues],
          decision: "escalated",
          diffBefore,
          diffAfter: "",
          judgmentSummary: "2体レビューの結果パースに失敗。人間のエスカレーションが必要。",
        });
        throw new DriftError(
          ESCALATION_LEVEL.LEVEL_3,
          "review_parse_failure",
          `2体レビューの結果パースに失敗しました。人間の確認が必要です。`,
        );
      }

      const toFix = this.reconcileReviews(reviewA, reviewB);

      if (toFix.length === 0) {
        this.records.push({
          step: "dual_claude",
          cycle,
          reviewer: "agent_a+agent_b",
          findings: [],
          decision: "lgtm",
          diffBefore,
          diffAfter: "",
          judgmentSummary: "指摘なし",
        });
        results.push(reviewA, reviewB);
        return results;
      }

      this.logger.log(EVENT.REVIEW_RECONCILED, {
        toFix: toFix.length,
        cycle,
      });

      await this.applyFixes(toFix, params);

      const diffAfter = params.getFileDiff
        ? await params.getFileDiff(params.targetFiles)
        : "";
      const judgmentSummary = await this.generateJudgmentSummary(toFix, diffBefore, diffAfter);

      this.records.push({
        step: "dual_claude",
        cycle,
        reviewer: "agent_a+agent_b",
        findings: toFix,
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

  private async selfReviewTestQuality(
    targetFiles: string[],
    specPath: string,
    testCasesPath: string,
  ): Promise<ReviewResult> {
    const fileContents = this.readFiles(targetFiles);
    const spec = readFileSync(specPath, "utf-8");
    const testCases = testCasesPath ? readFileSync(testCasesPath, "utf-8") : "";

    const prompt = `あなたはテストコードのレビュアーです。以下のテストコードを、テストケース文書と仕様書に照らして網羅的にレビューしてください。
該当する問題を全て一度に列挙してください。

## テストコード
${fileContents}

## テストケース文書
${testCases}

## 仕様書
${spec}

## 観点
- テストケース文書の全件がテストコードでカバーされているか
- テストケース文書にないテストを独自に追加していないか
- 1つのテストケースが複数のテスト関数に不要に分割されていないか（既存テストのアサート追加で済むものを別テストにしていないか）
- テスト種類ごとの検証焦点に応じた検証がされているか（基本動作は全フィールド、フィルタは含む/含まないの確認）

## レビュースコープの制約
- テストケースの追加提案はしない（テストケース文書にないテストの提案は design フェーズの責務）
- 仕様書のスコープ外セクションに記載された項目に関するテスト不足は指摘しない

## severity の判定基準
- critical: テストケース文書の項目が完全に欠落
- major: テストのアサーションが検証焦点を満たしていない、テストケース文書との不整合
- minor: テストの冗長性、命名の改善提案

## 回答形式
{"issues": [{"file": "ファイルパス", "line": 行番号, "severity": "critical|major|minor", "description": "指摘内容"}]}`;

    const result = await runClaude(
      { prompt, allowedTools: ["Read"], outputFormat: "json", timeoutMs: DEFAULT_TIMEOUT_MS },
      this.logger,
    );

    this.logger.log(EVENT.SELF_REVIEW, { step: "test_quality" });
    return this.parseReviewResult("test_self_quality", result.result);
  }

  private async selfReviewCriteria(
    targetFiles: string[],
    criteriaPaths: string[],
  ): Promise<ReviewResult> {
    const fileContents = this.readFiles(targetFiles);
    const criteria = criteriaPaths
      .map((p) => readFileSync(p, "utf-8"))
      .join("\n\n");

    const prompt = `以下のコードをレビュー観点に照らして網羅的にレビューしてください。
該当する違反を全て一度に列挙してください。一部だけ指摘して残りを次回に回さないでください。

## 対象ファイル
${fileContents}

## レビュースコープの制約
- テストケースの網羅性は指摘しない（テストケースの設計は design フェーズの責務であり、impl フェーズでは対象外）
- レビュー観点ファイルに記載のないリファクタリング提案はしない
- レビュー観点ファイルに記載のあるルール違反のみを指摘する

## severity の判定基準
- critical: 実行時エラーやデータ破損を引き起こすバグ
- major: 仕様との不整合、エラーハンドリング規約違反（握り潰し等）
- minor: 命名規則、マジックナンバー、関数行数超過などのスタイル違反

## 回答形式
指摘がある場合はJSON形式で回答してください:
{"issues": [{"file": "ファイルパス", "line": 行番号, "severity": "critical|major|minor", "description": "指摘内容"}]}
指摘がない場合は:
{"issues": []}`;

    const result = await runClaude(
      {
        prompt,
        allowedTools: ["Read"],
        appendSystemPrompt: criteria,
        outputFormat: "json",
        timeoutMs: DEFAULT_TIMEOUT_MS,
      },
      this.logger,
    );

    this.logger.log(EVENT.SELF_REVIEW, { step: "criteria" });
    return this.parseReviewResult("self_criteria", result.result);
  }

  private async selfReviewQuality(
    targetFiles: string[],
    specPath: string,
  ): Promise<ReviewResult> {
    const fileContents = this.readFiles(targetFiles);
    const spec = readFileSync(specPath, "utf-8");

    const prompt = `以下のコードにバグ、品質問題、仕様との不整合がないか網羅的にレビューしてください。
該当する問題を全て一度に列挙してください。一部だけ指摘して残りを次回に回さないでください。

## 対象ファイル
${fileContents}

## 仕様書
${spec}

## 観点
- 仕様書の受け入れ基準を全て満たしているか
- 仕様書の境界条件の定義と実装が一致しているか
- エラーハンドリングが適切か

## レビュースコープの制約
- テストケースの網羅性は指摘しない（テストケースの設計は design フェーズの責務であり、impl フェーズでは対象外）
- 仕様書に記載のない機能追加やリファクタリングは提案しない
- 仕様書の受け入れ基準と実装の不整合のみを指摘する

## severity の判定基準
- critical: 実行時エラーやデータ破損を引き起こすバグ
- major: 仕様との不整合、境界条件の処理が仕様と異なる
- minor: 仕様の意図からの軽微な逸脱

## 回答形式
{"issues": [{"file": "ファイルパス", "line": 行番号, "severity": "critical|major|minor", "description": "指摘内容"}]}`;

    const result = await runClaude(
      { prompt, allowedTools: ["Read"], outputFormat: "json", timeoutMs: DEFAULT_TIMEOUT_MS },
      this.logger,
    );

    this.logger.log(EVENT.SELF_REVIEW, { step: "quality" });
    return this.parseReviewResult("self_quality", result.result);
  }

  private async codexTestReview(
    targetFiles: string[],
    specPath: string,
    testCasesPath: string,
  ): Promise<ReviewResult> {
    const fileContents = this.readFiles(targetFiles);
    const spec = readFileSync(specPath, "utf-8");
    const testCases = testCasesPath ? readFileSync(testCasesPath, "utf-8") : "";

    const reviewPrompt = `以下のテストコードをレビューしてください。テストケース文書と仕様書に照らして、テストデータの妥当性と検証の正確性を確認してください。

## テストコード
${fileContents}

## テストケース文書
${testCases}

## 仕様書
${spec}

## レビュースコープの制約
- テストコードのみをレビューする。実装コードへの指摘はしない
- テストケースの追加提案はしない（design フェーズの責務）
- テストデータが仕様書の振る舞いを正しく検証しているかに集中する

JSON形式で回答: {"issues": [{"file": "パス", "line": 行番号, "severity": "critical|major|minor", "description": "内容"}]}`;

    const result = await this.execCodex(reviewPrompt);
    this.logger.logCommand("codex", ["test-review"], result);

    if (result.exitCode !== 0) {
      if (isCodexRateLimit(result)) {
        throw { stderr: result.stderr, code: result.exitCode };
      }
      throw new HarnessError(`Codex 実行失敗 (exit ${result.exitCode}): ${result.stderr}`);
    }

    return this.parseReviewResult("test_codex", result.stdout);
  }

  private async codexReview(
    targetFiles: string[],
    specPath: string,
  ): Promise<ReviewResult> {
    const fileContents = this.readFiles(targetFiles);
    const spec = readFileSync(specPath, "utf-8");

    const reviewPrompt = `以下のコードをレビューしてください。仕様書との整合性、バグ、品質問題を確認してください。

## 対象ファイル
${fileContents}

## 仕様書
${spec}

## レビュースコープの制約
- テストケースの網羅性は指摘しない（design フェーズの責務）
- 仕様書に記載のない機能追加やリファクタリングは提案しない
- 仕様書の「スコープ外」セクションに記載された項目に関する指摘はしない
- 仕様書の「境界条件」セクションで「許容する」「既知の制限」と明記されている振る舞いは指摘しない

JSON形式で回答: {"issues": [{"file": "パス", "line": 行番号, "severity": "critical|major|minor", "description": "内容"}]}`;

    const result = await this.execCodex(reviewPrompt);
    this.logger.logCommand("codex", ["review"], result);

    if (result.exitCode !== 0) {
      if (isCodexRateLimit(result)) {
        throw { stderr: result.stderr, code: result.exitCode };
      }
      // Codex の非ゼロ終了（未導入、クラッシュ等）はレビュー失敗として扱う
      throw new HarnessError(`Codex 実行失敗 (exit ${result.exitCode}): ${result.stderr}`);
    }

    return this.parseReviewResult("codex", result.stdout);
  }

  private async dualClaudeReview(
    targetFiles: string[],
    specPath: string,
  ): Promise<[ReviewResult, ReviewResult]> {
    const fileContents = this.readFiles(targetFiles);
    const spec = readFileSync(specPath, "utf-8");

    const prompt = `以下のコードにバグや品質問題がないかレビューしてください。

## 対象ファイル
${fileContents}

## 仕様書
${spec}

## レビュースコープの制約
- テストケースの網羅性は指摘しない（design フェーズの責務）
- 仕様書に記載のない機能追加やリファクタリングは提案しない

## 回答形式
{"issues": [{"file": "ファイルパス", "line": 行番号, "severity": "critical|major|minor", "description": "指摘内容"}]}`;

    const [resultA, resultB] = await Promise.all([
      runClaude(
        { prompt, allowedTools: ["Read"], outputFormat: "json", timeoutMs: DEFAULT_TIMEOUT_MS },
        this.logger,
      ),
      runClaude(
        { prompt, allowedTools: ["Read"], outputFormat: "json", timeoutMs: DEFAULT_TIMEOUT_MS },
        this.logger,
      ),
    ]);

    return [
      this.parseReviewResult("agent_a", resultA.result),
      this.parseReviewResult("agent_b", resultB.result),
    ];
  }

  reconcileReviews(
    a: ReviewResult,
    b: ReviewResult,
  ): ReviewIssue[] {
    // 全件残す方式: 両エージェントの指摘を統合し severity で判断
    // - critical/major: 常に修正対象
    // - minor: 両方が指摘した場合のみ修正対象
    const toFix: ReviewIssue[] = [];

    const allIssues = [
      ...a.issues.map((i) => ({ ...i, source: "A" as const })),
      ...b.issues.map((i) => ({ ...i, source: "B" as const })),
    ];

    for (const issue of allIssues) {
      if (issue.severity === "critical" || issue.severity === "major") {
        toFix.push(issue);
      } else {
        // minor: 相手側にも似た指摘があれば修正対象
        const otherIssues = issue.source === "A" ? b.issues : a.issues;
        const confirmedByOther = otherIssues.some(
          (other) => other.file === issue.file && other.description === issue.description,
        );
        if (confirmedByOther) {
          toFix.push(issue);
        } else {
          // 片方のみの minor → 対応不要として記録
          this.records.push({
            step: "dual_claude",
            cycle: 0,
            reviewer: issue.source === "A" ? "agent_a" : "agent_b",
            findings: [issue],
            decision: "accepted",
            diffBefore: "",
            diffAfter: "",
            judgmentSummary: `片方のエージェントのみが指摘した minor 指摘のため対応不要と判断`,
          });
        }
      }
    }

    return toFix;
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
          await this.applyFixes(result.issues, params);
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

      await this.applyFixes(result.issues, params);

      const diffAfter = params.getFileDiff
        ? await params.getFileDiff(params.targetFiles)
        : "";

      // 判断理由を claude -p で生成
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
  ): Promise<void> {
    const issueList = issues
      .map(
        (i, idx) =>
          `${idx + 1}. [${i.severity}] ${i.file}:${i.line ?? "?"} - ${i.description}`,
      )
      .join("\n");

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

    await runClaude(
      {
        prompt: `以下のレビュー指摘を修正してください。

## 指摘一覧
${issueList}

## 制約
${constraint}`,
        allowedTools: params.scopeAllowedTools,
        outputFormat: "json",
        cwd: this.projectRoot,
        timeoutMs: DEFAULT_TIMEOUT_MS,
      },
      this.logger,
    );

    // 修正でファイルが追加された可能性があるので再スキャン
    if (params.rescanFiles) {
      params.targetFiles = await params.rescanFiles();
    }

    // 対象ファイルが空ならリントをスキップ（全体に広がるのを防止）
    if (params.targetFiles.length > 0) {
      await this.lintGuard.check(params.targetFiles);
    }
    // テストレビュー時は実装が未生成のためテスト実行をスキップ
    if (params.reviewMode !== "test") {
      await this.runTests(params.testCommand);
    }
  }

  private async runTests(
    testCommand: string[],
  ): Promise<void> {
    const [cmd, ...args] = testCommand;
    try {
      await execFileAsync(cmd, args, {
        cwd: this.projectRoot,
        maxBuffer: 10 * 1024 * 1024,
        timeout: LOCAL_CMD_TIMEOUT_MS,
      });
    } catch (error: unknown) {
      const execError = error as { stderr?: string };
      throw new HarnessError(`テスト失敗: ${execError.stderr ?? "unknown error"}`);
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
      const result = await runClaude(
        {
          prompt: `以下のレビュー指摘に対してコード修正が行われました。なぜこの修正が必要だったのか、どういう判断で対応したかを3行以内で日本語で説明してください。

## レビュー指摘
${issueText}

## 修正前のdiff
${diffBefore.slice(0, 2000)}

## 修正後のdiff
${diffAfter.slice(0, 2000)}`,
          allowedTools: ["Read"],
          outputFormat: "json",
          timeoutMs: DEFAULT_TIMEOUT_MS,
        },
        this.logger,
      );
      return result.result;
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
      const result = await runClaude(
        {
          prompt: `あなたは第三者のコードレビュアーです。
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
{"safe": false, "reason": "判断理由"}`,
          allowedTools: ["Read"],
          outputFormat: "json",
          timeoutMs: DEFAULT_TIMEOUT_MS,
        },
        this.logger,
      );

      const cleaned = result.result.replace(/```(?:json)?\s*\n([\s\S]*?)```/g, "$1");
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

  private execCodex(prompt: string): Promise<CommandResult> {
    // prompt を stdin 経由で渡す（E2BIG 防止）
    return new Promise((resolve) => {
      const child = spawn(
        "codex",
        ["exec", "--full-auto", "--sandbox", "read-only", "--cd", this.projectRoot, "-"],
        { stdio: ["pipe", "pipe", "pipe"], timeout: CODEX_TIMEOUT_MS },
      );

      let stdout = "";
      let stderr = "";

      child.stdout.on("data", (chunk: Buffer) => {
        stdout += chunk.toString();
      });

      child.stderr.on("data", (chunk: Buffer) => {
        stderr += chunk.toString();
      });

      child.on("close", (code) => {
        const result: CommandResult = { stdout, stderr, exitCode: code ?? 1 };
        if (result.exitCode !== 0 && isCodexRateLimit(result)) {
          resolve(result);
          return;
        }
        resolve(result);
      });

      child.on("error", (err) => {
        resolve({ stdout, stderr: err.message, exitCode: 1 });
      });

      child.stdin.write(prompt);
      child.stdin.end();
    });
  }
}

function isCodexRateLimit(obj: unknown): boolean {
  if (!obj || typeof obj !== "object") return false;
  const stderr = (obj as { stderr?: string }).stderr ?? "";
  return /rate|limit|429/i.test(stderr);
}
