import { existsSync } from "node:fs";
import { resolve } from "node:path";
import type { Boundary } from "../boundary.ts";
import type { ResolvedProfileConfig } from "../config.ts";
import { assertReadyLikeStatus } from "../domain/plan-readiness.ts";
import type { TaskPlan } from "../types.ts";
import { GuardError } from "../types.ts";

export function validatePagePlan(
  boundary: Boundary,
  plan: TaskPlan,
): void {
  if (plan.type !== "page") {
    throw new GuardError(`page コマンドには type: page の plan が必要です。現在: ${plan.type ?? "未指定"}`);
  }
  if (!plan.profile) {
    throw new GuardError("page plan には profile が必要です。");
  }
  if (!plan.scope) {
    throw new GuardError("page plan には scope が必要です。");
  }
  if (!plan.specPath) {
    throw new GuardError("page plan には spec が必要です。");
  }
  if (!plan.testCasesPath) {
    throw new GuardError("page plan には test_cases が必要です。");
  }
  if (!plan.componentSpecPath) {
    throw new GuardError("page plan には component_spec が必要です。");
  }
  if (!plan.figmaCachePath) {
    throw new GuardError("page plan には figma_cache が必要です。");
  }
  if (plan.msw === undefined) {
    throw new GuardError("page plan には msw が必要です。");
  }
  if (plan.dependencies.length === 0) {
    throw new GuardError("page plan には Dependencies セクションが必要です。");
  }
  if (!plan.figmaSlice || plan.figmaSlice.trim() === "") {
    throw new GuardError("page plan には Figma Slice セクションが必要です。");
  }
  if (plan.browserScenarios.length === 0) {
    throw new GuardError("page plan には Browser Scenarios セクションが必要です。");
  }
  if (plan.targetTestCases.length === 0) {
    throw new GuardError("page plan には 対象テストケース セクションが必要です。");
  }
  if (plan.completionCriteria.length === 0) {
    throw new GuardError("page plan には 完了条件 セクションが必要です。");
  }

  boundary.validateScope(plan.scope);
  assertPlanFiles(boundary, [
    plan.specPath,
    plan.testCasesPath,
    plan.componentSpecPath,
    plan.figmaCachePath,
  ], "page");
  assertReadyLikeStatus(boundary.readFrontmatter(resolve(boundary.getProjectRoot(), plan.specPath)).status, "仕様書");
  assertReadyLikeStatus(
    boundary.readFrontmatter(resolve(boundary.getProjectRoot(), plan.testCasesPath)).status,
    "テストケース",
  );
  assertReadyLikeStatus(
    boundary.readFrontmatter(resolve(boundary.getProjectRoot(), plan.componentSpecPath)).status,
    "コンポーネント定義書",
  );
}

export function validateImplPlan(
  boundary: Boundary,
  plan: TaskPlan,
): void {
  if (plan.type !== "impl") {
    throw new GuardError(`impl コマンドには type: impl の plan が必要です。現在: ${plan.type ?? "未指定"}`);
  }
  if (!plan.profile) {
    throw new GuardError("impl plan には profile が必要です。");
  }
  if (!plan.scope) {
    throw new GuardError("impl plan には scope が必要です。");
  }
  if (!plan.specPath) {
    throw new GuardError("impl plan には spec が必要です。");
  }
  if (!plan.testCasesPath) {
    throw new GuardError("impl plan には test_cases が必要です。");
  }
  if (!plan.targetTestCases || plan.targetTestCases.length === 0) {
    throw new GuardError("impl plan には 対象テストケース セクションが必要です。");
  }

  boundary.validateScope(plan.scope);
  assertPlanFiles(boundary, [plan.specPath, plan.testCasesPath], "impl");
  assertReadyLikeStatus(boundary.readFrontmatter(resolve(boundary.getProjectRoot(), plan.specPath)).status, "仕様書");
  assertReadyLikeStatus(
    boundary.readFrontmatter(resolve(boundary.getProjectRoot(), plan.testCasesPath)).status,
    "テストケース",
  );
}

export function validateComponentPlan(
  boundary: Boundary,
  profile: ResolvedProfileConfig,
  plan: TaskPlan,
): void {
  if (plan.type !== "component") {
    throw new GuardError(`component コマンドには type: component の plan が必要です。現在: ${plan.type ?? "未指定"}`);
  }
  if (!plan.profile) {
    throw new GuardError("component plan には profile が必要です。");
  }
  if (!plan.scope) {
    throw new GuardError("component plan には scope が必要です。");
  }
  if (!plan.specPath) {
    throw new GuardError("component plan には spec が必要です。");
  }
  if (!plan.componentSpecPath) {
    throw new GuardError("component plan には component_spec が必要です。");
  }
  if (!plan.figmaCachePath) {
    throw new GuardError("component plan には figma_cache が必要です。");
  }
  if (plan.targets.length === 0) {
    throw new GuardError("component plan には Targets セクションが必要です。");
  }
  if (plan.dependencies.length === 0) {
    throw new GuardError("component plan には Dependencies セクションが必要です。");
  }
  if (!plan.figmaSlice || plan.figmaSlice.trim() === "") {
    throw new GuardError("component plan には Figma Slice セクションが必要です。");
  }
  if (plan.completionCriteria.length === 0) {
    throw new GuardError("component plan には 完了条件 セクションが必要です。");
  }

  boundary.validateScope(plan.scope);
  assertPlanFiles(boundary, [
    plan.specPath,
    plan.componentSpecPath,
    plan.figmaCachePath,
  ], "component");
  assertReadyLikeStatus(boundary.readFrontmatter(resolve(boundary.getProjectRoot(), plan.specPath)).status, "仕様書");
  assertReadyLikeStatus(
    boundary.readFrontmatter(resolve(boundary.getProjectRoot(), plan.componentSpecPath)).status,
    "コンポーネント定義書",
  );

  if (!profile.storybook) {
    throw new GuardError("component フローには profile.storybook.renderCommand / smokeCommand の設定が必要です。");
  }
}

function assertPlanFiles(
  boundary: Boundary,
  paths: string[],
  planType: "impl" | "page" | "component",
): void {
  const root = boundary.getProjectRoot();
  for (const path of paths) {
    const fullPath = resolve(root, path);
    boundary.assertWithinProject(fullPath);
    if (!existsSync(fullPath)) {
      throw new GuardError(`${planType} plan の参照ファイルが存在しません: ${fullPath}`);
    }
  }
}
