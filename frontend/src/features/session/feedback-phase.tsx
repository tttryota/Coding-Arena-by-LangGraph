import { PenLine, ArrowRight, Flag, Layers } from "lucide-react";
import { scoreLevel } from "@/lib/score";
import { ScoreBadge } from "@/components/common/score-badge";
import { Button } from "@/components/ui/button";
import type { SessionState } from "@/types/api";

interface FeedbackPhaseProps {
  sessionState: SessionState;
  onNext: () => void;
}

export function FeedbackPhase({ sessionState: s, onNext }: FeedbackPhaseProps) {
  const answers = s.answers ?? [];
  const latestAnswer = answers[answers.length - 1];
  const score = latestAnswer?.score ?? 0;
  const lvl = scoreLevel(score);
  const cpCount = s.confirmation_points?.length ?? 0;
  const cpIndex = (s.current_point_index ?? 0) + 1;
  const cpLabel = `確認ポイント ${cpIndex} / ${cpCount}`;
  const nextAction = s.next_action ?? "next";

  return (
    <>
      {/* Question number row — uses latestAnswer snapshot, not live state */}
      <div className="mb-3 flex items-center gap-2 font-mono text-[11px] font-medium uppercase tracking-widest text-muted-foreground">
        <span>問題</span>
        <span className="text-xs font-semibold text-foreground">
          {latestAnswer?.question_number ?? s.total_questions_asked ?? 1}
        </span>
        <span className="rounded-full bg-[rgb(51_65_85/0.5)] px-2 py-px font-sans text-[11px] normal-case tracking-normal text-muted-foreground">
          {cpLabel}
        </span>
      </div>

      {/* Question text (re-display) — uses latestAnswer snapshot */}
      <div className="rounded-md border border-border border-l-[3px] border-l-primary bg-[rgb(15_23_42/0.6)] px-5 py-[18px] text-[15px] leading-relaxed tracking-tight text-foreground">
        {latestAnswer?.question_text ?? s.current_question_text}
      </div>

      {/* User's answer echo */}
      {latestAnswer && (
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
          {latestAnswer?.feedback}
        </div>

        {/* Deepdive notice */}
        {nextAction === "deepdive" && s.confirmation_points && latestAnswer && (
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

        {/* Action buttons */}
        <div className="mt-[18px] flex justify-end gap-2">
          {nextAction === "complete" ? (
            <Button onClick={onNext}>
              <Flag className="h-3.5 w-3.5" />
              結果を見る
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
