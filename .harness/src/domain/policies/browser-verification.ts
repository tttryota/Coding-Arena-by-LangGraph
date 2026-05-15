import type { BrowserScenarioResult, BrowserVerificationResult, ReviewIssue } from "../../shared/types.ts";
import { HarnessError } from "../../shared/types.ts";

export function parseBrowserVerificationResult(output: string): BrowserVerificationResult {
  const cleaned = output.replace(/```(?:json)?\s*\n([\s\S]*?)```/g, "$1");
  const jsonMatch = /\{[\s\S]*"overall"\s*:\s*"[^"]+"[\s\S]*"scenarios"\s*:\s*\[[\s\S]*\][\s\S]*\}/.exec(cleaned);
  const raw = jsonMatch?.[0] ?? cleaned;

  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    throw new HarnessError("Browser Verification の出力が不正な JSON です。");
  }

  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
    throw new HarnessError("Browser Verification の出力形式が不正です。");
  }

  const record = parsed as Record<string, unknown>;
  if (record.overall !== "pass" && record.overall !== "fail" && record.overall !== "blocked") {
    throw new HarnessError("Browser Verification の overall は pass/fail/blocked のいずれかである必要があります。");
  }
  if (!Array.isArray(record.scenarios)) {
    throw new HarnessError("Browser Verification の scenarios は配列である必要があります。");
  }

  return {
    overall: record.overall,
    scenarios: record.scenarios.map((item, index) => parseBrowserScenarioResult(item, index)),
  } satisfies BrowserVerificationResult;
}

export function browserIssuesFromResult(result: BrowserVerificationResult): ReviewIssue[] {
  const issues = result.scenarios
    .filter((scenario) => scenario.status !== "pass")
    .map((scenario) => {
      const expected = scenario.expected?.join(" / ") ?? "期待結果不明";
      const observed = scenario.observed?.join(" / ") ?? "観測結果不明";
      const failureDetail = scenario.failedStep ? `失敗ステップ: ${scenario.failedStep}` : "失敗ステップ不明";
      return {
        description: `Browser Verification 失敗: ${scenario.name}. ${failureDetail}. expected=${expected}. observed=${observed}. ${scenario.notes ?? ""}`.trim(),
        severity: scenario.status === "blocked" ? "critical" : "major",
        file: "",
      } satisfies ReviewIssue;
    });

  if (issues.length === 0 && result.overall !== "pass") {
    issues.push({
      description: `Browser Verification 全体が ${result.overall} で終了しました。scenario 単位の詳細が返っていません。`,
      severity: "critical",
      file: "",
    });
  }

  return issues;
}

function parseBrowserScenarioResult(item: unknown, index: number): BrowserScenarioResult {
  if (typeof item !== "object" || item === null || Array.isArray(item)) {
    throw new HarnessError(`Browser Verification scenarios[${index}] の形式が不正です。`);
  }

  const record = item as Record<string, unknown>;
  const status = record.status;
  if (status !== "pass" && status !== "fail" && status !== "blocked") {
    throw new HarnessError(`Browser Verification scenarios[${index}].status は pass/fail/blocked のいずれかである必要があります。`);
  }

  return {
    name: requiredString(record.name, `scenarios[${index}].name`),
    status,
    completedSteps: optionalStringList(record.completed_steps),
    failedStep: optionalString(record.failed_step),
    expected: optionalStringList(record.expected),
    observed: optionalStringList(record.observed),
    notes: optionalString(record.notes),
  };
}

function requiredString(value: unknown, field: string): string {
  if (typeof value !== "string" || value.trim() === "") {
    throw new HarnessError(`Browser Verification の ${field} は空でない文字列である必要があります。`);
  }
  return value;
}

function optionalString(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() !== "" ? value : undefined;
}

function optionalStringList(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is string => typeof item === "string");
}
