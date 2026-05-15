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
    if (mode === "test") {
      return [
        "## 生成物の配置",
        "- この step では workspace 上のテストファイルを直接作成または更新すること",
        `- 主対象のテストファイル候補: ${this.suggestedTestFilePath(plan.scope)}`,
        "- 少なくとも 1 件は pytest/vitest が収集できる実テストケースを含めること",
        "- 回答本文だけでコードを返さず、ファイルへ反映すること",
        "- 主対象のテストファイルを早い段階で更新すること",
        "- repo 全体の監査や広い探索から始めず、対象ファイルの実装に集中すること",
        "- 実装内容の探索は import や公開インターフェース確認に必要な最小限に留めること",
      ].join("\n");
    }

    return [
      "## 生成物の配置",
      "- この step では workspace 上の実装ファイルを直接作成または更新すること",
      `- 主対象の実装ファイル候補: ${this.suggestedImplementationPath(plan.scope)}`,
      "- テストが import できる配置・モジュール名に合わせること",
      "- 回答本文だけでコードを返さず、ファイルへ反映すること",
      "- 主対象の実装ファイルを早い段階で更新すること",
      "- 広い探索や周辺ファイルの監査より、対象ファイルの実装に集中すること",
    ].join("\n");
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
