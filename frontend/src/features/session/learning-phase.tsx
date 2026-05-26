import { BookOpenText, ListChecks, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { SessionState } from "@/types/api";

interface LearningPhaseProps {
  sessionState: SessionState;
  onStartTest: () => void;
}

export function LearningPhase({
  sessionState: s,
  onStartTest,
}: LearningPhaseProps) {
  const points = s.confirmation_points ?? [];

  return (
    <div className="mx-auto max-w-[720px]">
      {/* Topic title */}
      <h1 className="mb-2 text-xl font-semibold tracking-tight">
        {s.roadmap_item_title}
      </h1>
      <p className="mb-6 text-sm text-muted-foreground">
        {s.roadmap_item_description}
      </p>

      {/* Overview card */}
      <div className="rounded-md border border-border border-l-[3px] border-l-[#38bdf8] bg-[rgb(15_23_42/0.6)] p-5">
        <div className="mb-2 flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wide text-[#38bdf8]">
          <BookOpenText className="h-3 w-3" />
          トピック概要
        </div>
        <div className="whitespace-pre-wrap text-[13.5px] leading-[1.75] text-foreground">
          {s.topic_overview}
        </div>
      </div>

      {/* Confirmation points preview */}
      {points.length > 0 && (
        <div className="mt-5 rounded-md border border-border bg-[rgb(15_23_42/0.4)] p-5">
          <div className="mb-3 flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
            <ListChecks className="h-3 w-3" />
            確認ポイント ({points.length} 問)
          </div>
          <ol className="flex flex-col gap-2">
            {points.map((cp, i) => (
              <li
                key={cp.id}
                className="flex items-start gap-2.5 text-[13px] leading-relaxed text-foreground"
              >
                <span className="mt-px flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[rgb(51_65_85/0.5)] font-mono text-[10px] font-semibold text-muted-foreground">
                  {i + 1}
                </span>
                <span>{cp.content}</span>
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Start test button */}
      <div className="mt-6 flex justify-center">
        <Button size="lg" onClick={onStartTest}>
          <Play className="h-4 w-4" />
          テスト開始
        </Button>
      </div>
    </div>
  );
}
