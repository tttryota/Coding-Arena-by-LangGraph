import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { resolve, join } from "node:path";
import { HarnessLogger, redact } from "./logger.ts";
import { LintGuard } from "./lint-guard.ts";
import { DriftGuard } from "./drift-guard.ts";
import { ReviewOrchestrator } from "./review-orchestrator.ts";
import type { Boundary } from "./boundary.ts";
import { runClaude } from "./claude-runner.ts";
import { GuardError, ESCALATION_LEVEL, EVENT } from "./types.ts";
import type { TaskPlan, ReviewRecord } from "./types.ts";
import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

const MAX_GREEN_RETRIES = 3;
const DEFAULT_TIMEOUT_MS = 10 * 60 * 1000;
const LOCAL_CMD_TIMEOUT_MS = 5 * 60 * 1000;

export class ImplFlow {
  private boundary: Boundary;

  constructor(boundary: Boundary) {
    this.boundary = boundary;
  }

  async run(planPath: string): Promise<void> {
    const plan = this.boundary.parsePlanFile(planPath);
    const root = this.boundary.getProjectRoot();
    const logger = new HarnessLogger(`impl_${plan.scope.replace(/\//g, "_")}`, { baseDir: join(root, "logs") });
    const lintGuard = new LintGuard(logger, root);
    const driftGuard = new DriftGuard(logger);
    const reviewOrchestrator = new ReviewOrchestrator(logger, lintGuard, root);

    // ガードチェック
    this.boundary.implementationGuard(plan);
    logger.log(EVENT.GUARD_CHECK, { scope: plan.scope, result: "pass" });

    // テストケース数から期待スコープ行数を推定（1テストケースあたり約30行）
    const LINES_PER_TEST_CASE = 30;
    const expectedLines = plan.targetTestCases.length * LINES_PER_TEST_CASE;
    driftGuard.startTask(plan.scope, expectedLines);
    const scopeTools = this.boundary.scopeAllowedTools(plan.scope);
    const testPath = this.boundary.testPathForScope(plan.scope);

    const spec = readFileSync(resolve(root, plan.specPath), "utf-8");
    const criteriaPaths = this.boundary.determineCriteriaPaths(plan.scope);
    const criteria = criteriaPaths.map((p) => readFileSync(p, "utf-8")).join("\n\n");

    logger.log(EVENT.TDD_START, { testCases: plan.targetTestCases });

    // テストコード一括生成
    console.log("テストコードを生成中...");
    const testGenResult = await runClaude(
      {
        prompt: `以下のテストケースに対応するpytestテストコードを書いてください。

## テストケース
${plan.targetTestCases.join("\n")}

## 仕様書
${spec}

## 制約
- テスト命名: test_{対象}_{条件}_{期待結果}
- 1テスト1関心事
- モックは外部依存のみ`,
        allowedTools: scopeTools,
        appendSystemPrompt: criteria,
        outputFormat: "json",
        cwd: root,
        timeoutMs: DEFAULT_TIMEOUT_MS,
      },
      logger,
    );

    // リントチェック
    await this.lintCheck(lintGuard, plan.scope, "テスト生成後");

    // RED 確認
    console.log("テスト実行中（RED確認）...");
    const redResult = await this.runTests(testPath);

    if (redResult.passed) {
      console.log("警告: テストが既にパスしています。実装生成をスキップしてレビューに進みます。");
      logger.log(EVENT.TEST_RUN, { result: "ALREADY_GREEN", output: redResult.output });
      await this.runReview(reviewOrchestrator, plan, criteriaPaths, testPath);
      this.generateReport(plan, logger, reviewOrchestrator.getRecords(), { greenAttempts: 0, alreadyGreen: true });
      console.log("完了しました。");
      return;
    }

    logger.log(EVENT.TEST_RUN, { result: "RED", output: redResult.output });

    // 実装 → GREEN リトライループ
    let sessionId = testGenResult.session_id;
    let lastFailureOutput = redResult.output;
    for (let attempt = 1; attempt <= MAX_GREEN_RETRIES; attempt++) {
      console.log(`実装コードを生成中... (試行 ${attempt}/${MAX_GREEN_RETRIES})`);

      const implPrompt = attempt === 1
        ? `テストを実行したところ失敗しました。テストをGREENにする実装を書いてください。

## テスト実行結果
${lastFailureOutput}

## 仕様書
${spec}

## 制約
- テストケースの範囲外の機能は実装しない
- 仕様書に記載のインターフェースに従う`
        : `前回の実装でもテストが失敗しました。別のアプローチで修正してください。

## テスト実行結果
${lastFailureOutput}

## 仕様書
${spec}`;

      const implResult = await runClaude(
        {
          prompt: implPrompt,
          allowedTools: scopeTools,
          appendSystemPrompt: criteria,
          resume: sessionId,
          outputFormat: "json",
          cwd: root,
          timeoutMs: DEFAULT_TIMEOUT_MS,
        },
        logger,
      );
      sessionId = implResult.session_id;

      // リントチェック
      await this.lintCheck(lintGuard, plan.scope, `実装後 (試行 ${attempt})`);

      // スコープ外変更の検証
      await this.boundary.verifyChangedFilesWithinScope(plan.scope);

      // GREEN 確認
      console.log("テスト実行中（GREEN確認）...");
      const greenResult = await this.runTests(testPath);
      logger.log(EVENT.TEST_RUN, {
        result: greenResult.passed ? "GREEN" : "FAILED",
        output: greenResult.output,
        attempt,
      });

      if (greenResult.passed) {
        driftGuard.checkTimeout();

        const diffLines = await this.boundary.countDiffLines();
        driftGuard.checkDiffScope(diffLines);

        // レビュー
        await this.runReview(reviewOrchestrator, plan, criteriaPaths, testPath);
        this.generateReport(plan, logger, reviewOrchestrator.getRecords(), { greenAttempts: attempt, alreadyGreen: false });
        console.log("完了しました。");
        return;
      }

      // 次の試行のために最新の失敗出力を保持
      lastFailureOutput = greenResult.output;

      // DriftGuard に失敗を記録
      const level = driftGuard.recordTestAttempt(plan.scope, false, greenResult.output);
      if (level !== null) {
        logger.log(EVENT.DRIFT_DETECTED, { metric: "green_failure", escalation: level, attempt });
        if (level >= ESCALATION_LEVEL.LEVEL_3) {
          // handleDrift が throw するのでここには来ないが念のため
          throw new GuardError("迷走検知: 人間のエスカレーションが必要です。");
        }
      }
    }

    throw new GuardError(
      `${MAX_GREEN_RETRIES} 回の試行でテストが GREEN になりませんでした。`,
    );
  }

  private async lintCheck(lintGuard: LintGuard, scope: string, phase: string): Promise<void> {
    console.log(`リントチェック中（${phase}）...`);
    const pyFiles = await this.boundary.findPythonFiles(scope);
    if (pyFiles.length > 0) {
      await lintGuard.check(pyFiles);
    }
  }

  private async runReview(
    orchestrator: ReviewOrchestrator,
    plan: TaskPlan,
    criteriaPaths: string[],
    testPath: string,
  ): Promise<void> {
    const pyFiles = await this.boundary.findPythonFiles(plan.scope);
    if (pyFiles.length === 0) return;

    console.log("レビュー実行中...");
    await orchestrator.runReview({
      targetFiles: pyFiles,
      specPath: resolve(this.boundary.getProjectRoot(), plan.specPath),
      criteriaPaths,
      testCommand: ["pytest", testPath, "-x", "--tb=short"],
      rescanFiles: () => this.boundary.findPythonFiles(plan.scope),
      scopeAllowedTools: this.boundary.scopeAllowedTools(plan.scope),
      getFileDiff: (files: string[]) => this.boundary.getFileDiff(files),
      designDecisions: plan.designDecisions,
    });
  }

  private async runTests(
    testPath: string,
  ): Promise<{ passed: boolean; output: string }> {
    try {
      const { stdout, stderr } = await execFileAsync(
        "pytest", [testPath, "-x", "--tb=short"],
        { cwd: this.boundary.getProjectRoot(), maxBuffer: 10 * 1024 * 1024, timeout: LOCAL_CMD_TIMEOUT_MS },
      );
      return { passed: true, output: stdout + stderr };
    } catch (error: unknown) {
      const execError = error as {
        stdout?: string;
        stderr?: string;
        code?: number | string;
      };
      const exitCode = typeof execError.code === "number" ? execError.code : 1;
      const output = (execError.stdout ?? "") + (execError.stderr ?? "");

      if (execError.code === "ENOENT") {
        throw new GuardError("pytest が見つかりません。インストールしてください。");
      }
      if (exitCode >= 2) {
        throw new GuardError(
          `pytest が内部エラーで終了しました (exit ${exitCode})。環境を確認してください。\n${output}`,
        );
      }

      return { passed: false, output };
    }
  }

  private generateReport(
    plan: TaskPlan,
    logger: HarnessLogger,
    records: ReviewRecord[],
    tdd: { greenAttempts: number; alreadyGreen: boolean },
  ): void {
    const root = this.boundary.getProjectRoot();
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
    const scopeSlug = plan.scope.replace(/\//g, "_");

    // review-data.json を保存
    logger.saveReviewData({ plan, records, tdd });

    // MD レポート生成
    // 集計対象: accepted を除いたレビュー実行レコードのみ
    const activeRecords = records.filter(
      (r) => r.step !== "design_decision" && r.decision !== "accepted",
    );
    const fixedRecords = activeRecords.filter((r) => r.decision === "fixed");
    const lgtmRecords = activeRecords.filter((r) => r.decision === "lgtm");
    const acceptedRecords = records.filter((r) => r.decision === "accepted");
    // レビューステップ数（ユニークな step で数える）
    const reviewSteps = [...new Set(activeRecords.map((r) => r.step))].length;
    // レビューサイクル総数（修正による再実行を含む）
    const totalCycles = activeRecords.length;
    // 修正した指摘の総件数（record 数ではなく issue 数）
    const fixCount = fixedRecords.reduce((sum, r) => sum + r.findings.length, 0);

    let md = `# タスクレポート: ${plan.scope}

**実行日**: ${timestamp}
**スコープ**: ${plan.scope}
**結果**: 完了
**レビューサイクル数**: ${totalCycles}回
**修正件数**: ${fixCount}件

## 対象テストケース
${plan.targetTestCases.map((tc, i) => `${i + 1}. ${tc}`).join("\n")}

## TDD サイクル
`;

    if (tdd.alreadyGreen) {
      md += `- テスト生成後、既に GREEN（実装生成スキップ）\n`;
    } else {
      md += `- 実装生成: ${tdd.greenAttempts}回目で GREEN（最大3回）\n`;
    }

    md += `\n---\n\n## レビュー詳細\n\n`;

    // ステップごとにグループ化（design_decision と accepted は別セクションで出力）
    const displayRecords = records.filter(
      (r) => r.step !== "design_decision" && r.decision !== "accepted",
    );
    const steps = [...new Set(displayRecords.map((r) => r.step))];
    for (const step of steps) {
      const stepRecords = displayRecords.filter((r) => r.step === step);
      md += `### ${step}\n\n`;

      for (const record of stepRecords) {
        if (record.decision === "lgtm") {
          md += `指摘なし（${record.cycle}回目で通過）\n\n`;
        } else if (record.decision === "fixed") {
          for (const issue of record.findings) {
            md += `#### 指摘: ${redact(issue.description)}（${issue.severity}）\n`;
            md += `- **ファイル**: ${issue.file}${issue.line ? `:${issue.line}` : ""}\n`;
            md += `- **判断**: 修正\n`;
            md += `- **理由**: ${redact(record.judgmentSummary)}\n`;
            if (record.diffAfter) {
              // diffAfter は修正直後に取得したスコープファイルの差分
              const snippet = redact(record.diffAfter.split("\n").slice(0, 30).join("\n"));
              if (snippet.trim()) {
                md += `- **修正内容**:\n\`\`\`diff\n${snippet}\n\`\`\`\n`;
              }
            }
            md += `\n`;
          }
        } else if (record.decision === "escalated") {
          md += `**エスカレーション**: ${record.judgmentSummary}\n\n`;
        }
      }
    }

    // 設計判断セクション（事前定義 vs レビュー中の許容を分離）
    const designDecisionRecords = acceptedRecords.filter((r) => r.step === "design_decision");
    const reviewAcceptedRecords = acceptedRecords.filter((r) => r.step !== "design_decision");

    if (designDecisionRecords.length > 0) {
      md += `---\n\n## 事前定義の設計判断\n\n`;
      for (const record of designDecisionRecords) {
        md += `- ${redact(record.judgmentSummary)}\n`;
      }
      md += `\n`;
    }

    if (reviewAcceptedRecords.length > 0) {
      md += `---\n\n## レビュー中に許容した指摘\n\n`;
      for (const record of reviewAcceptedRecords) {
        for (const issue of record.findings) {
          md += `#### ${redact(issue.description)}（${issue.severity}）\n`;
          md += `- **ファイル**: ${issue.file}${issue.line ? `:${issue.line}` : ""}\n`;
          md += `- **判断**: 許容\n`;
          md += `- **理由**: ${redact(record.judgmentSummary)}\n\n`;
        }
      }
    }

    // サマリー
    md += `---\n\n## サマリー\n\n`;
    md += `| 指標 | 値 |\n|---|---|\n`;
    md += `| レビューステップ数 | ${reviewSteps} |\n`;
    md += `| レビューサイクル総数 | ${totalCycles}回（修正による再実行を含む） |\n`;
    md += `| 修正した指摘数 | ${fixCount}件 |\n`;
    md += `| 通過ステップ数 | ${lgtmRecords.length}件 |\n`;
    md += `| 事前定義の設計判断 | ${designDecisionRecords.length}件 |\n`;
    md += `| レビュー中に許容 | ${reviewAcceptedRecords.length}件 |\n`;

    // 書き出し
    const reportsDir = join(root, "docs/reviews");
    mkdirSync(reportsDir, { recursive: true });
    const reportPath = join(reportsDir, `${timestamp}_${scopeSlug}.md`);
    writeFileSync(reportPath, md, "utf-8");
    console.log(`レポート生成: ${reportPath}`);
  }
}
