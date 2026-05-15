import { HarnessError } from "../types.ts";
import type { ReviewIssue, ReviewResult } from "../types.ts";

export function parseReviewResult(reviewer: string, output: string): ReviewResult {
  try {
    const parsed = parseJsonObject(output, (cleaned) => {
      const jsonMatch = /\{[^{}]*"issues"\s*:\s*\[[\s\S]*?\]\s*\}/.exec(cleaned);
      if (!jsonMatch) {
        throw new HarnessError(`レビュー出力からJSONを抽出できませんでした (reviewer: ${reviewer})`);
      }
      return JSON.parse(jsonMatch[0]) as Record<string, unknown>;
    });

    if (!Array.isArray(parsed.issues)) {
      throw new HarnessError(`issues フィールドが配列ではありません (reviewer: ${reviewer})`);
    }

    const validatedIssues: ReviewIssue[] = [];
    let invalidCount = 0;
    for (const item of parsed.issues) {
      if (
        typeof item === "object" && item !== null &&
        typeof (item as Record<string, unknown>).description === "string" &&
        typeof (item as Record<string, unknown>).severity === "string" &&
        typeof (item as Record<string, unknown>).file === "string"
      ) {
        const issue = item as Record<string, unknown>;
        validatedIssues.push({
          description: issue.description as string,
          severity: (["critical", "major", "minor"].includes(issue.severity as string)
            ? issue.severity : "major") as "critical" | "major" | "minor",
          file: issue.file as string,
          line: typeof issue.line === "number" ? issue.line : undefined,
        });
      } else {
        invalidCount++;
      }
    }

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
    return {
      reviewer,
      issues: [
        {
          description: "レビュー結果のパースに失敗しました。出力を手動確認してください。",
          severity: "critical",
          file: "",
        },
      ],
      isLgtm: false,
    };
  }
}

export function parseMinorAcceptanceVerdict(output: string): { safe: boolean; reason: string } {
  const parsed = parseJsonObject(output);
  return {
    safe: typeof parsed.safe === "boolean" ? parsed.safe : true,
    reason: typeof parsed.reason === "string" ? parsed.reason : "（判断理由なし）",
  };
}

function parseJsonObject(
  output: string,
  fallback?: (cleaned: string) => Record<string, unknown>,
): Record<string, unknown> {
  const cleaned = output.replace(/```(?:json)?\s*\n([\s\S]*?)```/g, "$1");
  try {
    return JSON.parse(cleaned) as Record<string, unknown>;
  } catch {
    if (!fallback) throw new HarnessError("JSON parse failed");
    return fallback(cleaned);
  }
}
