import { Check, CheckCircle2, Lightbulb } from "lucide-react";
import { scoreLevel } from "@/lib/score";
import type { SessionState, QuizAnswerRecord } from "@/types/api";
import type { QuizPhase } from "./use-quiz-session-store";

interface SessionProgressProps {
  sessionState: SessionState;
  phase: QuizPhase;
}

interface Step {
  kind: "done" | "current" | "upcoming";
  n: number;
  label: string;
  score?: number;
  color?: string;
  bg?: string;
  typing?: string;
}

function shortQ(text: string): string {
  const m = text.match(/^[^、。\n]{1,28}/);
  const prefix = m ? m[0] : text.slice(0, 28);
  return prefix + (text.length > 28 ? "…" : "");
}

export function SessionProgress({
  sessionState: s,
  phase,
}: SessionProgressProps) {
  const answers = s.answers ?? [];
  const asked = s.total_questions_asked ?? 1;
  const total = 20; // estimated total
  const cpCount = s.confirmation_points?.length ?? 0;
  const cpIndex = (s.current_point_index ?? 0) + 1;

  // Build step list
  const steps: Step[] = [];

  // Past answers
  for (const a of answers) {
    const lvl = scoreLevel(a.score);
    steps.push({
      kind: "done",
      n: a.question_number,
      label: shortQ(a.question_text),
      score: a.score,
      color: lvl.fg,
      bg: lvl.bg,
    });
  }

  // Current question
  if (
    phase === "question" ||
    phase === "chat_response" ||
    phase === "explanation"
  ) {
    const cp = s.confirmation_points?.[s.current_point_index ?? 0];
    steps.push({
      kind: "current",
      n: asked,
      label: cp?.content ?? "",
      typing:
        phase === "explanation"
          ? "解説中…"
          : phase === "chat_response"
            ? "対話中…"
            : "回答中…",
    });
  } else if (phase === "feedback") {
    // Show current as just-answered
    const latest = answers[answers.length - 1];
    if (latest && steps[steps.length - 1]?.n !== asked) {
      const lvl = scoreLevel(latest.score);
      steps.push({
        kind: "done",
        n: asked,
        label: shortQ(latest.question_text),
        score: latest.score,
        color: lvl.fg,
        bg: lvl.bg,
      });
    }
  }

  // Upcoming placeholders
  const upcomingStart = asked + 1;
  const ghostCount = Math.min(4, total - steps.length);
  for (let i = 0; i < ghostCount; i++) {
    steps.push({ kind: "upcoming", n: upcomingStart + i, label: "未出題" });
  }

  const pct = total > 0 ? Math.round((asked / total) * 100) : 0;
  const avgScore =
    answers.length > 0
      ? Math.round(
          answers.reduce((sum: number, a: QuizAnswerRecord) => sum + a.score, 0) /
            answers.length,
        )
      : 0;

  return (
    <aside className="sticky top-2 hidden flex-col gap-3 rounded-lg border border-border bg-card p-4 min-[1180px]:flex">
      {/* Header */}
      <div className="flex items-center justify-between">
        <span className="text-[13px] font-semibold tracking-tight text-foreground">
          進捗
        </span>
        <span className="font-mono text-[11px] tabular-nums text-muted-foreground">
          {asked}{" "}
          <span className="text-muted-foreground">/ 約{total}問</span>
        </span>
      </div>

      {/* Progress bar */}
      <div className="h-1 overflow-hidden rounded-full bg-[rgb(30_41_59/0.8)]">
        <div
          className="h-full rounded-full bg-primary transition-[width] duration-300 ease-out"
          style={{ width: `${pct}%` }}
        />
      </div>

      {/* Steps */}
      <div className="-mx-2 -mb-1 mt-1 flex max-h-[420px] flex-col gap-0.5 overflow-y-auto px-2 pb-1">
        {steps.map((step, i) => (
          <div
            key={i}
            className={`grid grid-cols-[18px_28px_1fr_auto] items-center gap-2 rounded-md px-2 py-[7px] text-[12.5px] transition-colors duration-[120ms] ${
              step.kind === "current"
                ? "bg-[rgb(59_130_246/0.1)]"
                : "hover:bg-[rgb(51_65_85/0.35)]"
            }`}
          >
            {/* Dot */}
            <span
              className={`inline-flex h-3.5 w-3.5 items-center justify-center rounded-full ${
                step.kind === "done"
                  ? "bg-[rgb(51_65_85/0.8)] text-foreground"
                  : step.kind === "current"
                    ? "relative bg-primary"
                    : "border-[1.5px] border-[rgb(51_65_85/0.9)] bg-transparent"
              }`}
            >
              {step.kind === "done" && (
                <Check className="h-[9px] w-[9px] text-slate-50" />
              )}
              {step.kind === "current" && (
                <span className="absolute inset-[-3px] animate-[qs-pulse_1.6s_ease-in-out_infinite] rounded-full bg-[rgb(37_99_235/0.3)]" />
              )}
            </span>

            {/* Q number */}
            <span
              className={`text-right font-mono text-[11px] font-medium tabular-nums ${
                step.kind === "upcoming"
                  ? "text-muted-foreground"
                  : "text-foreground"
              }`}
            >
              Q{step.n}
            </span>

            {/* Label */}
            <span
              className={`min-w-0 truncate ${
                step.kind === "done"
                  ? "text-foreground"
                  : step.kind === "current"
                    ? "font-medium text-foreground"
                    : "text-muted-foreground"
              }`}
              title={step.label}
            >
              {step.label}
            </span>

            {/* Score or typing */}
            {step.kind === "done" && step.score !== undefined && (
              <span
                className="rounded-full px-1.5 py-px font-mono text-[11px] font-semibold tabular-nums"
                style={{ color: step.color, background: step.bg }}
              >
                {step.score}
              </span>
            )}
            {step.kind === "current" && (
              <span className="text-[11px] italic text-primary">
                {step.typing}
              </span>
            )}
            {step.kind === "upcoming" && <span />}
          </div>
        ))}
      </div>

      {/* Convergence notice */}
      {asked >= 18 && (
        <div className="mt-1 flex items-center gap-1.5 rounded-md border border-[rgb(245_158_11/0.22)] bg-[rgb(245_158_11/0.08)] px-2.5 py-2 text-[11px] leading-snug text-[#fbbf24]">
          <CheckCircle2 className="h-3 w-3 shrink-0" />
          <span>まもなく完了します</span>
        </div>
      )}

      {/* Footer stats */}
      <div className="flex flex-col gap-1.5 border-t border-border pt-3">
        <div className="flex items-center justify-between text-[11px] text-muted-foreground">
          <span>これまでの平均</span>
          <span>
            <b className="font-mono font-semibold tabular-nums text-foreground">
              {avgScore}
            </b>
          </span>
        </div>
        <div className="flex items-center justify-between text-[11px] text-muted-foreground">
          <span>確認ポイント</span>
          <span>
            <b className="font-mono font-semibold tabular-nums text-foreground">
              {cpIndex}
            </b>{" "}
            / {cpCount}
          </span>
        </div>
      </div>

      {/* Tip */}
      <div className="rounded-md border-l-2 border-border bg-[rgb(30_41_59/0.5)] px-2.5 py-2 text-[11px] leading-normal text-muted-foreground">
        <Lightbulb className="mr-1 inline h-[11px] w-[11px]" />
        わからない時は{" "}
        <kbd className="mx-0.5 rounded border border-input bg-[rgb(15_23_42/0.7)] px-[5px] py-px font-mono text-[10px] text-foreground">
          解説して
        </kbd>{" "}
        ボタンを。チャットで自由に質問もできます。
      </div>
    </aside>
  );
}
