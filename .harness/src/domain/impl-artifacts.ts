import type { TaskPlan } from "../types.ts";

type ScopePathResolver = {
  extractName(scope: string): string;
  sourcePathForScope(scope: string): string;
  testPathForScope(scope: string): string;
};

export class ImplArtifactsPolicy {
  private testFrameworkName: string;
  private paths: ScopePathResolver;

  constructor(testFrameworkName: string, paths: ScopePathResolver) {
    this.testFrameworkName = testFrameworkName;
    this.paths = paths;
  }

  resolveRuleName(plan: TaskPlan): string | undefined {
    if (plan.type === "impl" && plan.profile === "frontend") {
      return "logic";
    }
    return plan.type;
  }

  buildMswInstructions(plan: TaskPlan, mode: "test" | "impl"): string {
    if (!plan.msw) return "";

    if (mode === "test") {
      return `## MSW セットアップ
- テストファイルに MSW server のセットアップ (beforeAll/afterEach/afterAll) を含める
- API モック用の handler import を含める（handler ファイルは実装フェーズで生成される）
- handler の配置先: frontend/src/mocks/handlers/
- server.use(...handlers) でモックを適用する`;
    }

    return `## MSW ハンドラ生成
- frontend/src/mocks/handlers/ に共有ハンドラファイルを生成する
- ハンドラのレスポンス形状はバックエンド API の契約と一致させる
- テストファイルから import されるパスと一致させる`;
  }

  isGenerationBenchmark(plan: TaskPlan): boolean {
    return plan.benchmarkMode === "generation";
  }

  suggestedTestFilePath(scope: string): string {
    const testDir = this.paths.testPathForScope(scope);
    const moduleName = this.scopeModuleName(scope);
    if (this.testFrameworkName === "pytest") {
      return `${testDir}/test_${moduleName}.py`;
    }
    if (this.testFrameworkName === "vitest") {
      return `${testDir}/${this.paths.extractName(scope)}.test.ts`;
    }
    return `${testDir}/`;
  }

  suggestedImplementationPath(scope: string): string {
    const sourceDir = this.paths.sourcePathForScope(scope);
    const moduleName = this.scopeModuleName(scope);
    if (this.testFrameworkName === "pytest") {
      return `${sourceDir}/${moduleName}.py`;
    }
    if (this.testFrameworkName === "vitest") {
      return `${sourceDir}/${this.paths.extractName(scope)}.ts`;
    }
    return `${sourceDir}/`;
  }

  buildArtifactInstructions(plan: TaskPlan, mode: "test" | "impl"): string {
    const generationBenchmarkDiscipline = this.isGenerationBenchmark(plan)
      ? [
          "## Generation Benchmark Discipline",
          "- 既に置かれている placeholder ファイルをそのまま置換すること",
          "- 参照してよい一次情報は spec、approved test cases、対象の placeholder ファイル、および言語設定ファイルまでに限定すること",
          "- docs/reviews や過去の benchmark レポートは参照しないこと",
          "- 最低限の確認が済んだらすぐに対象ファイルへ書き込みを開始すること",
        ].join("\n")
      : "";
    const generationTestDiscipline = this.isGenerationBenchmark(plan) && mode === "test"
      ? [
          "- 最初に主対象のテストファイルを placeholder から置換すること",
          "- この step で書き込む先は主対象のテストファイルに限定すること",
          "- repo 全体の充足確認や既存 concrete test の監査だけで終わらないこと",
          "- 実装内容の探索は import や公開インターフェース確認に必要な最小限に留めること",
        ].join("\n")
      : "";

    if (mode === "test") {
      return [
        "## 生成物の配置",
        "- この step では workspace 上のテストファイルを直接作成または更新すること",
        `- 主対象のテストファイル候補: ${this.suggestedTestFilePath(plan.scope)}`,
        "- 少なくとも 1 件は pytest/vitest が収集できる実テストケースを含めること",
        "- 回答本文だけでコードを返さず、ファイルへ反映すること",
        generationBenchmarkDiscipline,
        generationTestDiscipline,
      ].join("\n");
    }

    return [
      "## 生成物の配置",
      "- この step では workspace 上の実装ファイルを直接作成または更新すること",
      `- 主対象の実装ファイル候補: ${this.suggestedImplementationPath(plan.scope)}`,
      "- テストが import できる配置・モジュール名に合わせること",
      "- 回答本文だけでコードを返さず、ファイルへ反映すること",
      generationBenchmarkDiscipline,
    ].join("\n");
  }

  buildTestPlaceholderContent(): string {
    if (this.testFrameworkName === "pytest") {
      return [
        "\"\"\"Harness placeholder: replace with concrete pytest cases for this scope.\"\"\"",
        "",
        "def test_harness_placeholder() -> None:",
        "    raise AssertionError(\"Replace this placeholder with concrete benchmark tests.\")",
        "",
      ].join("\n");
    }
    if (this.testFrameworkName === "vitest") {
      return [
        "import { describe, it, expect } from \"vitest\";",
        "",
        "describe(\"harness placeholder\", () => {",
        "  it(\"must be replaced with concrete benchmark tests\", () => {",
        "    expect(false, \"replace placeholder tests\").toBe(true);",
        "  });",
        "});",
        "",
      ].join("\n");
    }
    return [
      "# Harness placeholder: replace with concrete tests for this scope.",
      "",
    ].join("\n");
  }

  buildImplementationPlaceholderContent(): string {
    if (this.testFrameworkName === "pytest") {
      return [
        "\"\"\"Harness placeholder: replace with the concrete implementation for this scope.\"\"\"",
        "",
      ].join("\n");
    }
    return "// Harness placeholder: replace with the concrete implementation for this scope.\n";
  }

  countTestIntents(fileContents: string): number {
    if (this.testFrameworkName === "pytest") {
      const matches = fileContents.match(/^\s*def\s+test_[A-Za-z0-9_]+\s*\(/gm);
      return matches?.length ?? 0;
    }
    if (this.testFrameworkName === "vitest") {
      const matches = fileContents.match(/\b(?:it|test)\s*\(/g);
      return matches?.length ?? 0;
    }
    return 0;
  }

  private scopeModuleName(scope: string): string {
    return this.paths.extractName(scope).replace(/-/g, "_");
  }
}
