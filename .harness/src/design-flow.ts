import { readFileSync, existsSync } from "node:fs";
import { join } from "node:path";
import type { HarnessLogger } from "./logger.ts";
import type { Boundary } from "./boundary.ts";
import { runClaude } from "./claude-runner.ts";
import { GuardError } from "./types.ts";

const DEFAULT_TIMEOUT_MS = 10 * 60 * 1000;

export class DesignFlow {
  private boundary: Boundary;

  constructor(boundary: Boundary) {
    this.boundary = boundary;
  }

  async run(featureName: string, requirements: string, logger: HarnessLogger): Promise<void> {
    const root = this.boundary.getProjectRoot();
    const category = this.boundary.extractCategory(featureName);
    const name = this.boundary.extractName(featureName);

    // design-flow の書き込み先を仕様書/テストケースディレクトリに限定
    const specAllowedTools = [
      "Read",
      `Write(docs/spec/${category}/*)`,
      `Edit(docs/spec/${category}/*)`,
    ];
    const tcAllowedTools = [
      "Read",
      `Write(tests/test-cases/${category}/*)`,
      `Edit(tests/test-cases/${category}/*)`,
    ];

    // 仕様書
    const specPath = join(root, "docs/spec", category, `${name}.md`);
    if (existsSync(specPath)) {
      console.log(`仕様書は既に存在します: ${specPath}`);
    } else {
      await this.generateSpec(featureName, specPath, requirements, specAllowedTools, logger);
      if (!existsSync(specPath)) {
        throw new GuardError(`仕様書が生成されませんでした: ${specPath}`);
      }
      console.log(`仕様書を生成しました: ${specPath}`);
    }

    const specFm = this.boundary.readFrontmatter(specPath);
    if (specFm.status !== "approved") {
      console.log("仕様書を確認し、frontmatter の status を approved に更新してから再実行してください。");
      return;
    }

    // テストケース
    const tcPath = join(root, "tests/test-cases", category, `${name}.md`);
    if (existsSync(tcPath)) {
      console.log(`テストケースは既に存在します: ${tcPath}`);
    } else {
      await this.generateTestCases(featureName, specPath, tcPath, tcAllowedTools, logger);
      if (!existsSync(tcPath)) {
        throw new GuardError(`テストケースが生成されませんでした: ${tcPath}`);
      }
      console.log(`テストケースを生成しました: ${tcPath}`);
    }

    const tcFm = this.boundary.readFrontmatter(tcPath);
    if (tcFm.status !== "approved") {
      console.log("テストケースを確認し、frontmatter の status を approved に更新してください。");
      return;
    }

    console.log("仕様書・テストケースともに承認済みです。impl フローに進めます。");
  }

  private async generateSpec(
    featureName: string, outputPath: string, requirements: string,
    allowedTools: string[], logger: HarnessLogger,
  ): Promise<void> {
    const root = this.boundary.getProjectRoot();
    const templatePath = join(root, "docs/spec/TEMPLATE.md");
    const template = existsSync(templatePath) ? readFileSync(templatePath, "utf-8") : "";
    const claudeMd = this.readClaudeMd();

    await runClaude(
      {
        prompt: `以下の要件から機能仕様書を作成してください。

## 要件
${requirements}

## 出力先
${outputPath}

## feature名
${featureName}

## テンプレート
${template}

## 制約
- 必ず上記の出力先パスにファイルを作成すること
- 5〜15個のテストケースが書ける粒度にする
- 他の仕様書を読まなくても実装に着手できる独立性
- 依存は他コンポーネントのインターフェース参照のみ`,
        allowedTools,
        appendSystemPrompt: claudeMd,
        outputFormat: "json",
        cwd: root,
        timeoutMs: DEFAULT_TIMEOUT_MS,
      },
      logger,
    );
  }

  private async generateTestCases(
    featureName: string, specPath: string, outputPath: string,
    allowedTools: string[], logger: HarnessLogger,
  ): Promise<void> {
    const root = this.boundary.getProjectRoot();
    const spec = readFileSync(specPath, "utf-8");
    const templatePath = join(root, "tests/test-cases/TEMPLATE.md");
    const template = existsSync(templatePath) ? readFileSync(templatePath, "utf-8") : "";

    await runClaude(
      {
        prompt: `以下の仕様書からテストケースを導出してください。

## 仕様書
${spec}

## 出力先
${outputPath}

## feature名
${featureName}

## テンプレート
${template}

## 制約
- 必ず上記の出力先パスにファイルを作成すること
- 正常系・境界系・異常系を網羅
- Phase分け（最小骨格 → コアロジック → エッジケース → 外部連携）
- 実装順序を考慮した並び
- 重複がないこと`,
        allowedTools,
        outputFormat: "json",
        cwd: root,
        timeoutMs: DEFAULT_TIMEOUT_MS,
      },
      logger,
    );
  }

  private readClaudeMd(): string {
    const claudeMdPath = join(this.boundary.getProjectRoot(), "CLAUDE.md");
    return existsSync(claudeMdPath) ? readFileSync(claudeMdPath, "utf-8") : "";
  }
}
