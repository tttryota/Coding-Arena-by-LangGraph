import { readFileSync } from "node:fs";
import { loadTemplate, renderTemplate } from "../../infrastructure/templates.ts";
import type { RunnerRegistry } from "../../infrastructure/runners/runner-registry.ts";
import type { LintViolation, ReviewIssue } from "../../shared/types.ts";

type PromptPackage = {
  prompt: string;
  appendSystemPrompt?: string;
};

type ApplyFixPromptParams = {
  targetFiles: string[];
  specPath: string;
  testCasesPath?: string;
  criteriaPaths: string[];
  diffBefore?: string;
};

export class ReviewPromptFactory {
  private projectRoot: string;
  private registry: RunnerRegistry;

  constructor(projectRoot: string, registry: RunnerRegistry) {
    this.projectRoot = projectRoot;
    this.registry = registry;
  }

  buildComponentCriteriaReview(
    targetFiles: string[],
    criteriaPaths: string[],
  ): PromptPackage {
    return this.buildCriteriaReview("review-impl-criteria", targetFiles, criteriaPaths);
  }

  buildTestQualityReview(
    targetFiles: string[],
    specPath: string,
    testCasesPath: string,
  ): PromptPackage {
    return this.renderPrompt("review-test-quality", {
      fileContents: this.renderFiles(targetFiles),
      testCases: this.readOptionalFile(testCasesPath),
      spec: readFileSync(specPath, "utf-8"),
      responseFormat: this.responseFormat(),
    });
  }

  buildImplementationCriteriaReview(
    targetFiles: string[],
    criteriaPaths: string[],
  ): PromptPackage {
    return this.buildCriteriaReview("review-impl-criteria", targetFiles, criteriaPaths);
  }

  buildImplementationQualityReview(
    targetFiles: string[],
    specPath: string,
  ): PromptPackage {
    return this.renderPrompt("review-impl-quality", {
      fileContents: this.renderFiles(targetFiles),
      spec: readFileSync(specPath, "utf-8"),
      responseFormat: this.responseFormat(),
    });
  }

  buildCodexTestReview(
    targetFiles: string[],
    specPath: string,
    testCasesPath: string,
  ): PromptPackage {
    return this.renderPrompt("review-codex-test", {
      fileContents: this.renderFiles(targetFiles),
      testCases: this.readOptionalFile(testCasesPath),
      spec: readFileSync(specPath, "utf-8"),
      responseFormat: this.responseFormat(),
    });
  }

  buildCodexImplementationReview(
    targetFiles: string[],
    specPath: string,
  ): PromptPackage {
    return this.renderPrompt("review-codex-impl", {
      fileContents: this.renderFiles(targetFiles),
      spec: readFileSync(specPath, "utf-8"),
      responseFormat: this.responseFormat(),
    });
  }

  buildPageDesignReview(
    targetFiles: string[],
    specPath: string,
    componentSpecPath: string,
    dependenciesText: string,
    figmaSlice: string,
  ): PromptPackage {
    return this.renderPrompt("review-page-design", {
      fileContents: this.renderFiles(targetFiles),
      spec: readFileSync(specPath, "utf-8"),
      componentSpec: readFileSync(componentSpecPath, "utf-8"),
      dependencies: dependenciesText,
      figmaSlice,
      responseFormat: this.responseFormat(),
    });
  }

  buildPageBehaviorReview(
    targetFiles: string[],
    specPath: string,
    browserScenariosText: string,
  ): PromptPackage {
    return this.renderPrompt("review-page-behavior", {
      fileContents: this.renderFiles(targetFiles),
      spec: readFileSync(specPath, "utf-8"),
      browserScenarios: browserScenariosText,
      responseFormat: this.responseFormat(),
    });
  }

  buildPageCodeReview(
    targetFiles: string[],
    criteriaPaths: string[],
  ): PromptPackage {
    return this.buildCriteriaReview("review-impl-criteria", targetFiles, criteriaPaths);
  }

  buildApplyFixesPrompt(
    issues: ReviewIssue[],
    params: ApplyFixPromptParams,
  ): string {
    const issueList = issues
      .map(
        (issue, index) =>
          `${index + 1}. [${issue.severity}] ${issue.file}:${issue.line ?? "?"} - ${issue.description}`,
      )
      .join("\n");
    const criteria = params.criteriaPaths.length > 0
      ? this.readJoinedFiles(params.criteriaPaths)
      : "";
    const testCases = params.testCasesPath
      ? this.readOptionalFile(params.testCasesPath)
      : "";
    const hasBugFix = issues.some((issue) => issue.severity === "critical" || issue.severity === "major");
    const constraint = hasBugFix
      ? `- バグ修正の場合は振る舞いの変更を許可する
- 仕様書に記載された振る舞いに合致させること
- 既存テストが壊れた場合はテストも修正する`
      : `- 指摘された箇所のみ修正
- 既存テストを壊さない
- 振る舞いを変えない（リファクタリングのみ）`;

    return [
      "以下のレビュー指摘を修正してください。",
      "## 指摘一覧",
      issueList,
      "## 現在の対象ファイル",
      this.renderFiles(params.targetFiles),
      "## 仕様書",
      readFileSync(params.specPath, "utf-8"),
      testCases ? `## 承認済みテストケース\n${testCases}` : "",
      criteria ? `## レビュー観点\n${criteria}` : "",
      params.diffBefore ? `## 直前の差分\n${params.diffBefore}` : "",
      "## 制約",
      constraint,
      "- issue 解消だけでなく、今回触ったファイルの lint/type も通る状態にする",
      "- repo 全体の探索や pytest 実行方法の探索は始めず、対象ファイルの修正に集中する",
      "- 明らかな lint/type 違反を新たに作らない",
    ].filter((section) => section !== "").join("\n\n");
  }

  buildLintFixPrompt(
    violations: LintViolation[],
    targetFiles: string[],
  ): string {
    const lintIssueList = violations
      .map((violation, index) => `${index + 1}. ${violation.tool}: ${violation.file}:${violation.line} - ${violation.message}`)
      .join("\n");
    return [
      "以下の lint/type 違反を修正してください。",
      "## 違反一覧",
      lintIssueList,
      "## 現在の対象ファイル",
      this.renderFiles(targetFiles),
      "## 制約",
      "- 違反が出ている対象ファイルだけを修正する",
      "- レビュー指摘で直した契約や振る舞いを壊さない",
      "- `try`-`except`-`pass` や例外握り潰しで違反を回避しない",
    ].join("\n\n");
  }

  buildJudgmentSummaryPrompt(
    issues: ReviewIssue[],
    diffBefore: string,
    diffAfter: string,
  ): string {
    const issueText = issues
      .map((issue) => `[${issue.severity}] ${issue.file}:${issue.line ?? "?"} - ${issue.description}`)
      .join("\n");

    return `以下のレビュー指摘に対してコード修正が行われました。なぜこの修正が必要だったのか、どういう判断で対応したかを3行以内で日本語で説明してください。

## レビュー指摘
${issueText}

## 修正前のdiff
${diffBefore.slice(0, 2000)}

## 修正後のdiff
${diffAfter.slice(0, 2000)}`;
  }

  buildMinorAcceptancePrompt(
    issues: ReviewIssue[],
    diffHistory: string,
    specPath: string,
  ): string {
    const issueText = issues
      .map((issue) => `[${issue.severity}] ${issue.file}:${issue.line ?? "?"} - ${issue.description}`)
      .join("\n");
    const spec = readFileSync(specPath, "utf-8");

    return `あなたは第三者のコードレビュアーです。
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
  }

  private buildCriteriaReview(
    templateName: string,
    targetFiles: string[],
    criteriaPaths: string[],
  ): PromptPackage {
    const rendered = this.renderPrompt(templateName, {
      fileContents: this.renderFiles(targetFiles),
      responseFormat: this.responseFormat(),
    });
    return {
      ...rendered,
      appendSystemPrompt: this.readJoinedFiles(criteriaPaths),
    };
  }

  private renderPrompt(
    templateName: string,
    vars: Record<string, string>,
  ): PromptPackage {
    const config = this.registry.getConfig();
    const template = loadTemplate(templateName, this.projectRoot, config.templates);
    return {
      prompt: renderTemplate(template, vars),
    };
  }

  private responseFormat(): string {
    const config = this.registry.getConfig();
    return loadTemplate("review-response-format", this.projectRoot, config.templates);
  }

  private renderFiles(files: string[]): string {
    return files
      .map((file) => {
        const content = readFileSync(file, "utf-8");
        return `### ${file}\n\`\`\`\n${content}\n\`\`\``;
      })
      .join("\n\n");
  }

  private readJoinedFiles(paths: string[]): string {
    return paths.map((path) => readFileSync(path, "utf-8")).join("\n\n");
  }

  private readOptionalFile(path: string): string {
    return path ? readFileSync(path, "utf-8") : "";
  }
}
