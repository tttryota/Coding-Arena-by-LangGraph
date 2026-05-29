import {
  PenLine,
  ArrowRight,
  Flag,
  Layers,
  RotateCcw,
  ChevronRight,
} from "lucide-react";
import { scoreLevel } from "@/lib/score";
import { ScoreBadge } from "@/components/common/score-badge";
import { Button } from "@/components/ui/button";
import type {
  SessionState,
  CodingDifficultyType,
} from "@/types/api";

interface FeedbackPhaseProps {
  sessionState: SessionState;
  onNext: () => void;
  /** Coding session: score from current evaluation */
  codingScore?: number;
  /** Coding session: feedback text from current evaluation */
  codingFeedback?: string;
  /** Coding session: next action routing */
  codingNextAction?: "next_step" | "retry" | "next_cp" | "complete";
  /** Coding session: current format for display (from snapshot) */
  codingFormat?: CodingDifficultyType;
  /** Coding session: question text at submission time (snapshot) */
  codingQuestionText?: string;
  /** Coding session: question number at submission time (snapshot) */
  codingQuestionNumber?: number;
  /** Snapshot CP index at submission time (0-based) — coding or quiz */
  snapshotCpIndex?: number;
}

const FORMAT_LABELS: Record<CodingDifficultyType, string> = {
  rewrite: "書き換え",
  fill_blank: "穴埋め",
  bug_fix: "バグ修正",
  extend: "拡張",
  implement: "実装",
};

const FORMAT_COLORS: Record<CodingDifficultyType, { text: string; bg: string }> = {
  rewrite: { text: "#34d399", bg: "rgb(52 211 153 / 0.12)" },
  fill_blank: { text: "#38bdf8", bg: "rgb(56 189 248 / 0.12)" },
  bug_fix: { text: "#fb923c", bg: "rgb(251 146 60 / 0.12)" },
  extend: { text: "#a78bfa", bg: "rgb(167 139 250 / 0.12)" },
  implement: { text: "#f472b6", bg: "rgb(244 114 182 / 0.12)" },
};

export function FeedbackPhase({
  sessionState: s,
  onNext,
  codingScore,
  codingFeedback,
  codingNextAction,
  codingFormat,
  codingQuestionText,
  codingQuestionNumber,
  snapshotCpIndex,
}: FeedbackPhaseProps) {
  const isCoding = codingScore != null;

  // Score / feedback source
  const answers = s.answers ?? [];
  const latestAnswer = answers[answers.length - 1];
  const score = isCoding ? codingScore : (latestAnswer?.score ?? 0);
  const feedback = isCoding ? codingFeedback : latestAnswer?.feedback;
  const lvl = scoreLevel(score);

  const cpCount = s.confirmation_points?.length ?? 0;
  const rawCpIndex = snapshotCpIndex ?? (s.current_point_index ?? 0);
  const cpIndex = Math.min(rawCpIndex + 1, cpCount);
  const cpLabel = `確認ポイント ${cpIndex} / ${cpCount}`;

  // Next action
  const nextAction = isCoding ? codingNextAction : (s.next_action ?? "next");
  const isComplete = nextAction === "complete";

  return (
    <>
      {/* Question number row */}
      <div className="mb-3 flex items-center gap-2 font-mono text-[11px] font-medium uppercase tracking-widest text-muted-foreground">
        <span>問題</span>
        <span className="text-xs font-semibold text-foreground">
          {isCoding
            ? (codingQuestionNumber ?? s.total_questions_asked ?? 1)
            : (latestAnswer?.question_number ?? s.total_questions_asked ?? 1)}
        </span>
        <span className="rounded-full bg-[rgb(51_65_85/0.5)] px-2 py-px font-sans text-[11px] normal-case tracking-normal text-muted-foreground">
          {cpLabel}
        </span>
        {codingFormat != null && (
          <>
            <span className="flex-1" />
            <span
              className="rounded-full px-2 py-px font-sans text-[11px] normal-case tracking-normal"
              style={{
                color: FORMAT_COLORS[codingFormat].text,
                background: FORMAT_COLORS[codingFormat].bg,
              }}
            >
              {FORMAT_LABELS[codingFormat]}
            </span>
          </>
        )}
      </div>

      {/* Question text (re-display) — use snapshot for coding to avoid showing next question */}
      <div className="rounded-md border border-border border-l-[3px] border-l-primary bg-[rgb(15_23_42/0.6)] px-5 py-[18px] text-[15px] leading-relaxed tracking-tight text-foreground">
        {isCoding
          ? (codingQuestionText ?? s.current_question_text)
          : (latestAnswer?.question_text ?? s.current_question_text)}
      </div>

      {/* User's answer echo (quiz mode only) */}
      {!isCoding && latestAnswer && (
        <div className="mt-4">
          <div className="mb-1.5 flex items-center gap-2 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
            <PenLine className="h-3 w-3" />
            <span>あなたの回答</span>
          </div>
          {latestAnswer.answer_type === "code" ? (
            <pre className="m-0 overflow-x-auto whitespace-pre-wrap rounded-md border border-[rgb(51_65_85/0.5)] bg-[#0b1220] px-3.5 py-3 font-mono text-[12.5px] leading-relaxed text-[#e2e8f0]">
              {latestAnswer.answer_text}
            </pre>
          ) : (
            <div className="rounded-md border border-border bg-[rgb(2_6_23/0.4)] px-3.5 py-3 text-[13.5px] leading-relaxed text-foreground">
              {latestAnswer.answer_text}
            </div>
          )}
        </div>
      )}

      {/* Feedback card */}
      <div className="mt-[18px] animate-[bubble-in_220ms_ease-out] rounded-lg border border-border bg-[rgb(15_23_42/0.6)] p-5">
        {/* Score header */}
        <div className="mb-3.5 flex items-center justify-between gap-3">
          <div className="flex items-baseline gap-3">
            <span
              className="font-mono text-4xl font-semibold tabular-nums leading-none tracking-tight"
              style={{ color: lvl.fg }}
            >
              {score}
            </span>
            <div>
              <div className="mb-1 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                スコア
              </div>
              <ScoreBadge score={score} />
            </div>
          </div>
          <div className="h-1.5 w-[120px] overflow-hidden rounded-full bg-[rgb(30_41_59/0.8)]">
            <div
              className="h-full rounded-full"
              style={{ width: `${score}%`, background: lvl.fg }}
            />
          </div>
        </div>

        {/* Feedback body */}
        <div className="mb-1 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
          フィードバック
        </div>
        <div className="rounded-md border-l-2 border-l-[rgb(51_65_85/0.7)] bg-[rgb(2_6_23/0.5)] px-4 py-3.5 text-[13.5px] leading-[1.75] text-foreground">
          {feedback}
        </div>

        {/* Quiz deepdive notice */}
        {!isCoding && nextAction === "deepdive" && s.confirmation_points && latestAnswer && (
          <div className="mt-3.5 flex items-start gap-2.5 rounded-md border border-[rgb(59_130_246/0.22)] bg-[rgb(59_130_246/0.07)] px-3 py-2.5 text-[13px] leading-normal text-[#93c5fd]">
            <Layers className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#60a5fa]" />
            <span>
              <b className="font-semibold text-[#dbeafe]">
                理解を深めるための追加の問題があります。
              </b>{" "}
              {(() => {
                const cp = s.confirmation_points.find(
                  (p) => p.id === latestAnswer.confirmation_point_id,
                );
                return cp
                  ? `この確認ポイント（${cp.content}）について、別の角度から問います。`
                  : "別の角度から問います。";
              })()}
            </span>
          </div>
        )}

        {/* Coding next action notice */}
        {isCoding && nextAction === "next_step" && (
          <div className="mt-3.5 flex items-start gap-2.5 rounded-md border border-[rgb(52_211_153/0.22)] bg-[rgb(52_211_153/0.07)] px-3 py-2.5 text-[13px] leading-normal text-[#6ee7b7]">
            <ChevronRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#34d399]" />
            <span>
              <b className="font-semibold text-[#d1fae5]">
                難易度が上がります。
              </b>{" "}
              同じ確認ポイントで、より実践的な形式に進みます。
            </span>
          </div>
        )}
        {isCoding && nextAction === "retry" && (
          <div className="mt-3.5 flex items-start gap-2.5 rounded-md border border-[rgb(251_146_60/0.22)] bg-[rgb(251_146_60/0.07)] px-3 py-2.5 text-[13px] leading-normal text-[#fdba74]">
            <RotateCcw className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#fb923c]" />
            <span>
              <b className="font-semibold text-[#fed7aa]">
                もう一度挑戦しましょう。
              </b>{" "}
              フィードバックを参考に、同じ形式で再挑戦できます。
            </span>
          </div>
        )}
        {isCoding && nextAction === "next_cp" && (
          <div className="mt-3.5 flex items-start gap-2.5 rounded-md border border-[rgb(59_130_246/0.22)] bg-[rgb(59_130_246/0.07)] px-3 py-2.5 text-[13px] leading-normal text-[#93c5fd]">
            <Layers className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#60a5fa]" />
            <span>
              <b className="font-semibold text-[#dbeafe]">
                次の確認ポイントに進みます。
              </b>
            </span>
          </div>
        )}

        {/* Action buttons */}
        <div className="mt-[18px] flex justify-end gap-2">
          {isComplete ? (
            <Button onClick={onNext}>
              <Flag className="h-3.5 w-3.5" />
              結果を見る
            </Button>
          ) : nextAction === "retry" ? (
            <Button onClick={onNext} variant="outline">
              <RotateCcw className="h-3.5 w-3.5" />
              もう一度挑戦
            </Button>
          ) : (
            <Button onClick={onNext}>
              <ArrowRight className="h-3.5 w-3.5" />
              次の問題へ
            </Button>
          )}
        </div>
      </div>
    </>
  );
}
