import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import type { HarnessLogger } from "../logger.ts";
import { redact } from "../logger.ts";
import type { ReviewRecord, TaskPlan } from "../types.ts";

type TddSummary = {
  greenAttempts: number;
  alreadyGreen: boolean;
  invalidReason?: string;
};

export function writeImplReport(
  projectRoot: string,
  logger: HarnessLogger,
  plan: TaskPlan,
  records: ReviewRecord[],
  tdd: TddSummary,
): void {
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
  const scopeSlug = plan.scope.replace(/\//g, "_");
  const usageSummary = logger.summarizeRunnerUsage();

  logger.saveReviewData({
    plan,
    benchmark: {
      mode: plan.benchmarkMode ?? null,
      invalidReason: tdd.invalidReason ?? null,
    },
    records,
    tdd,
    usageSummary,
  });

  const activeRecords = records.filter(
    (record) => record.step !== "design_decision" && record.decision !== "accepted",
  );
  const fixedRecords = activeRecords.filter((record) => record.decision === "fixed");
  const lgtmRecords = activeRecords.filter((record) => record.decision === "lgtm");
  const acceptedRecords = records.filter((record) => record.decision === "accepted");
  const reviewSteps = [...new Set(activeRecords.map((record) => record.step))].length;
  const totalCycles = activeRecords.length;
  const fixCount = fixedRecords.reduce((sum, record) => sum + record.findings.length, 0);

  let md = `# タスクレポート: ${plan.scope}

**実行日**: ${timestamp}
**スコープ**: ${plan.scope}
**結果**: 完了
**ベンチマーク種別**: ${plan.benchmarkMode ?? "none"}
**レビューサイクル数**: ${totalCycles}回
**修正件数**: ${fixCount}件
**LLM実行回数**: ${usageSummary.total.runs}回

## 対象テストケース
${plan.targetTestCases.map((testCase, index) => `${index + 1}. ${testCase}`).join("\n")}

## TDD サイクル
`;

  if (tdd.alreadyGreen) {
    md += "- テスト生成後、既に GREEN（実装生成スキップ）\n";
  } else {
    md += `- 実装生成: ${tdd.greenAttempts}回目で GREEN（最大3回）\n`;
  }
  if (tdd.invalidReason) {
    md += `- benchmark 判定: 無効（${tdd.invalidReason}）\n`;
  }

  md += "\n---\n\n## レビュー詳細\n\n";

  const displayRecords = records.filter(
    (record) => record.step !== "design_decision" && record.decision !== "accepted",
  );
  const steps = [...new Set(displayRecords.map((record) => record.step))];
  for (const step of steps) {
    const stepRecords = displayRecords.filter((record) => record.step === step);
    md += `### ${step}\n\n`;

    for (const record of stepRecords) {
      if (record.decision === "lgtm") {
        md += `指摘なし（${record.cycle}回目で通過）\n\n`;
      } else if (record.decision === "fixed") {
        for (const issue of record.findings) {
          md += `- [${issue.severity}] ${issue.file}${issue.line ? `:${issue.line}` : ""} — ${redact(issue.description)}\n`;
        }
        md += `\n**判断**: ${redact(record.judgmentSummary)}\n`;
        if (record.diffAfter) {
          const snippet = redact(record.diffAfter.split("\n").slice(0, 30).join("\n"));
          if (snippet.trim()) {
            md += `\n<details><summary>修正 diff</summary>\n\n\`\`\`diff\n${snippet}\n\`\`\`\n</details>\n`;
          }
        }
        md += "\n";
      } else if (record.decision === "escalated") {
        md += `**エスカレーション**: ${record.judgmentSummary}\n\n`;
      }
    }
  }

  const designDecisionRecords = acceptedRecords.filter((record) => record.step === "design_decision");
  const reviewAcceptedRecords = acceptedRecords.filter((record) => record.step !== "design_decision");

  if (designDecisionRecords.length > 0) {
    md += "---\n\n## 事前定義の設計判断\n\n";
    for (const record of designDecisionRecords) {
      md += `- ${redact(record.judgmentSummary)}\n`;
    }
    md += "\n";
  }

  if (reviewAcceptedRecords.length > 0) {
    md += "---\n\n## レビュー中に許容した指摘\n\n";
    for (const record of reviewAcceptedRecords) {
      for (const issue of record.findings) {
        md += `#### ${redact(issue.description)}（${issue.severity}）\n`;
        md += `- **ファイル**: ${issue.file}${issue.line ? `:${issue.line}` : ""}\n`;
        md += "- **判断**: 許容\n";
        md += `- **理由**: ${redact(record.judgmentSummary)}\n\n`;
      }
    }
  }

  md += "---\n\n## サマリー\n\n";
  md += "| 指標 | 値 |\n|---|---|\n";
  md += `| レビューステップ数 | ${reviewSteps} |\n`;
  md += `| レビューサイクル総数 | ${totalCycles}回（修正による再実行を含む） |\n`;
  md += `| 修正した指摘数 | ${fixCount}件 |\n`;
  md += `| 通過ステップ数 | ${lgtmRecords.length}件 |\n`;
  md += `| 事前定義の設計判断 | ${designDecisionRecords.length}件 |\n`;
  md += `| レビュー中に許容 | ${reviewAcceptedRecords.length}件 |\n`;
  md += `| LLM実行回数 | ${usageSummary.total.runs}件 |\n`;
  md += `| Input Tokens | ${usageSummary.total.inputTokens} |\n`;
  md += `| Output Tokens | ${usageSummary.total.outputTokens} |\n`;
  md += `| Cost USD | ${usageSummary.total.costUsd.toFixed(4)} |\n`;

  const usageSteps = Object.entries(usageSummary.byStep);
  if (usageSteps.length > 0) {
    md += "\n### LLM Usage By Step\n\n";
    md += "| Step | Runs | Input | Output | Cost USD |\n|---|---:|---:|---:|---:|\n";
    for (const [step, totals] of usageSteps) {
      md += `| ${step} | ${totals.runs} | ${totals.inputTokens} | ${totals.outputTokens} | ${totals.costUsd.toFixed(4)} |\n`;
    }
  }

  const reportsDir = join(projectRoot, "docs/reviews");
  mkdirSync(reportsDir, { recursive: true });
  const reportPath = join(reportsDir, `${timestamp}_${scopeSlug}.md`);
  writeFileSync(reportPath, md, "utf-8");
  console.log(`レポート生成: ${reportPath}`);
}
