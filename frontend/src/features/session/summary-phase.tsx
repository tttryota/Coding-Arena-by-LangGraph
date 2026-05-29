import { useState } from "react";
import { CheckCircle2, ChevronRight, ArrowLeft, TrendingUp } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { scoreLevel } from "@/lib/score";
import { ScoreBadge } from "@/components/common/score-badge";
import { Button } from "@/components/ui/button";
import type { QuizAnswerRecord } from "@/types/api";

interface SummaryPhaseProps {
  answers: QuizAnswerRecord[];
  onBack: () => void;
  /** Coding session: final score */
  codingScore?: number;
  /** Coding session: total questions attempted */
  codingTotalQuestions?: number;
}

const TIER_COLORS: Record<string, string> = {
  not_started: "#94a3b8",
  insufficient: "#fb7185",
  partial: "#fbbf24",
  sufficient: "#34d399",
};

const TIER_LABELS: Record<string, string> = {
  not_started: "未着手",
  insufficient: "不十分",
  partial: "部分的",
  sufficient: "十分",
};

export function SummaryPhase({
  answers,
  onBack,
  codingScore,
  codingTotalQuestions,
}: SummaryPhaseProps) {
  const isCoding = codingScore != null;
  const [expandedIdx, setExpandedIdx] = useState<number>(-1);

  const avg = isCoding
    ? codingScore
    : answers.length > 0
      ? Math.round(answers.reduce((a, x) => a + x.score, 0) / answers.length)
      : 0;
  const lvl = scoreLevel(avg);
  const totalCount = isCoding ? (codingTotalQuestions ?? 0) : answers.length;

  // Tier distribution
  const tiers: Record<string, number> = {
    not_started: 0,
    insufficient: 0,
    partial: 0,
    sufficient: 0,
  };
  for (const a of answers) {
    tiers[scoreLevel(a.score).key]++;
  }

  return (
    <div className="mx-auto max-w-[820px]">
      {/* Header */}
      <div className="mb-6 text-center">
        <div className="mb-3 inline-flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-widest text-muted-foreground">
          <CheckCircle2 className="h-3 w-3" style={{ color: "var(--color-score-sufficient-fg)" }} />
          <span>セッション完了</span>
        </div>
        <div className="mb-1.5 text-[28px] font-semibold tracking-tight text-foreground">
          お疲れさまでした
        </div>
        <div className="text-[13px] leading-normal text-muted-foreground">
          {isCoding
            ? `${totalCount} 問のコーディング演習を完了しました。`
            : `${totalCount} 問の回答を評価しました。各問の詳細は下の一覧から確認できます。`}
        </div>
      </div>

      {/* Score card */}
      <div className="mb-7 grid grid-cols-[auto_1fr] items-center gap-8 rounded-xl border border-border bg-card p-7">
        <div>
          <div className="mb-2 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
            {isCoding ? "最終スコア" : "総合スコア"}
          </div>
          <div
            className="font-mono text-[80px] font-semibold leading-none tracking-tighter tabular-nums"
            style={{ color: lvl.fg }}
          >
            {avg}
            <small className="ml-1 text-[22px] font-medium text-muted-foreground">
              /100
            </small>
          </div>
          <div className="mt-2">
            <ScoreBadge score={avg} />
          </div>
        </div>
        <div className="flex min-w-0 flex-col gap-3">
          {/* Progress */}
          <div>
            <div className="mb-1.5 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
              達成度
            </div>
            <div className="h-2.5 overflow-hidden rounded-full bg-[rgb(30_41_59/0.8)]">
              <div
                className="h-full rounded-full transition-[width] duration-[800ms] ease-out"
                style={{ width: `${avg}%`, background: lvl.fg }}
              />
            </div>
          </div>

          {/* Distribution (quiz mode only) */}
          {!isCoding && (
          <div>
            <div className="mb-1.5 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
              スコア分布
            </div>
            <div className="flex h-2 overflow-hidden rounded-full bg-[rgb(30_41_59/0.6)]">
              {Object.entries(tiers).map(
                ([k, v]) =>
                  v > 0 && (
                    <span
                      key={k}
                      className="block h-full"
                      style={{
                        width: `${(v / answers.length) * 100}%`,
                        background: TIER_COLORS[k],
                      }}
                    />
                  ),
              )}
            </div>
            <div className="mt-2 flex flex-wrap gap-3.5 text-[11px] text-muted-foreground">
              {Object.entries(tiers).map(([k, v]) => (
                <span key={k} className="inline-flex items-center gap-1">
                  <span
                    className="inline-block h-2 w-2 rounded-full"
                    style={{ background: TIER_COLORS[k] }}
                  />
                  {TIER_LABELS[k]}{" "}
                  <b className="font-mono font-semibold text-foreground">{v}</b>
                </span>
              ))}
            </div>
          </div>
          )}

          {/* Stats */}
          <div className="flex gap-6 text-xs text-muted-foreground">
            <span>
              <b className="mr-1 font-mono text-sm font-semibold text-foreground">
                {totalCount}
              </b>
              問
            </span>
          </div>
        </div>
      </div>

      {/* Answer list (quiz mode only) */}
      {!isCoding && answers.length > 0 && (
        <>
          <div className="mb-3 flex items-center justify-between text-[13px] font-semibold text-foreground">
            <span>回答一覧</span>
            <span className="font-normal text-muted-foreground">クリックで展開</span>
          </div>

          <ScrollArea className="max-h-[480px] overflow-hidden rounded-lg border border-border bg-card">
            {answers.map((a, i) => {
              const aLvl = scoreLevel(a.score);
              const expanded = i === expandedIdx;
              return (
                <div key={i}>
                  <div
                    className={`grid cursor-pointer grid-cols-[36px_1fr_auto_auto_auto] items-center gap-3.5 border-b border-border px-[18px] py-3.5 transition-colors duration-150 hover:bg-[rgb(51_65_85/0.22)] ${i === answers.length - 1 && !expanded ? "border-b-0" : ""}`}
                    onClick={() => setExpandedIdx(expanded ? -1 : i)}
                  >
                    <span className="rounded bg-[rgb(30_41_59/0.7)] py-1 text-center font-mono text-[11px] font-semibold text-muted-foreground">
                      Q{a.question_number}
                    </span>
                    <span className="min-w-0 truncate text-[13px] text-foreground">
                      {a.question_text}
                    </span>
                    <span className="rounded border border-border px-1.5 py-px font-mono text-[10px] tracking-wide text-muted-foreground">
                      {a.answer_type === "code" ? "CODE" : "TEXT"}
                    </span>
                    <span className="inline-flex items-center gap-2">
                      <span
                        className="font-mono text-[13px] font-semibold"
                        style={{ color: aLvl.fg }}
                      >
                        {a.score}
                      </span>
                      <ScoreBadge score={a.score} />
                    </span>
                    <ChevronRight
                      className={`h-3.5 w-3.5 text-muted-foreground transition-transform duration-150 ${expanded ? "rotate-90" : ""}`}
                    />
                  </div>
                  {expanded && (
                    <div className="border-b border-border bg-[rgb(2_6_23/0.4)] px-[18px] pb-[18px]">
                      <div className="grid grid-cols-[80px_1fr] gap-x-5 gap-y-3.5 pt-3.5">
                        <div className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                          問題
                        </div>
                        <div className="whitespace-pre-wrap text-[13px] leading-[1.7] text-foreground">
                          {a.question_text}
                        </div>
                        <div className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                          あなたの回答
                        </div>
                        {a.answer_type === "code" ? (
                          <pre className="overflow-x-auto whitespace-pre-wrap rounded-md border border-[rgb(51_65_85/0.5)] bg-[#0b1220] px-3.5 py-3 font-mono text-[12.5px] leading-relaxed text-[#e2e8f0]">
                            {a.answer_text}
                          </pre>
                        ) : (
                          <div className="whitespace-pre-wrap text-[13px] leading-[1.7] text-foreground">
                            {a.answer_text}
                          </div>
                        )}
                        <div className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                          フィードバック
                        </div>
                        <div className="text-[13px] leading-[1.7] text-foreground">
                          {a.feedback}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </ScrollArea>
        </>
      )}

      {/* Actions */}
      <div className="mt-7 flex flex-wrap items-center justify-between gap-3">
        <div className="text-xs text-muted-foreground">
          <TrendingUp className="mr-1 inline h-3 w-3 align-middle" />
          項目スコアが更新されました
        </div>
        <Button onClick={onBack}>
          <ArrowLeft className="h-3.5 w-3.5" />
          ロードマップに戻る
        </Button>
      </div>
    </div>
  );
}
