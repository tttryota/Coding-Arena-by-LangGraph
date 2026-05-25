import { BookOpenText, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { SessionState } from "@/types/api";

interface ExplanationPhaseProps {
  sessionState: SessionState;
  explanationText: string;
  /** 解説対象の問題文（ライブ state ではなくスナップショット） */
  questionText: string;
  /** 解説対象の問題番号（ライブ state ではなくスナップショット） */
  questionNumber: number;
  onContinue: () => void;
}

export function ExplanationPhase({
  sessionState: s,
  explanationText,
  questionText,
  questionNumber,
  onContinue,
}: ExplanationPhaseProps) {
  const cpCount = s.confirmation_points?.length ?? 0;
  const cpIndex = (s.current_point_index ?? 0) + 1;
  const cpLabel = `確認ポイント ${cpIndex} / ${cpCount}`;

  return (
    <>
      {/* Question number row — uses snapshot props */}
      <div className="mb-3 flex items-center gap-2 font-mono text-[11px] font-medium uppercase tracking-widest text-muted-foreground">
        <span>問題</span>
        <span className="text-xs font-semibold text-foreground">
          {questionNumber}
        </span>
        <span className="rounded-full bg-[rgb(51_65_85/0.5)] px-2 py-px font-sans text-[11px] normal-case tracking-normal text-muted-foreground">
          {cpLabel}
        </span>
      </div>

      {/* Question text (snapshot) */}
      <div className="rounded-md border border-border border-l-[3px] border-l-primary bg-[rgb(15_23_42/0.6)] px-5 py-[18px] text-[15px] leading-relaxed tracking-tight text-foreground">
        {questionText}
      </div>

      {/* Explanation card */}
      <div className="mt-[18px] animate-[bubble-in_220ms_ease-out] rounded-md border border-border border-l-[3px] border-l-[#fbbf24] bg-[rgb(15_23_42/0.6)] p-5">
        <div className="mb-2 flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wide text-[#fbbf24]">
          <BookOpenText className="h-3 w-3" />
          解説
        </div>
        <div className="whitespace-pre-wrap text-[13.5px] leading-[1.75] text-foreground">
          {explanationText}
        </div>
        <div className="mt-[18px] flex justify-end gap-2">
          <Button onClick={onContinue}>
            <Check className="h-3.5 w-3.5" />
            理解した、続ける
          </Button>
        </div>
      </div>
    </>
  );
}
