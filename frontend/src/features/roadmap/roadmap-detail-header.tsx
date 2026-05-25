import { scoreLevel } from "@/lib/score";
import { ScoreBadge } from "@/components/common/score-badge";

interface RoadmapDetailHeaderProps {
  topic: string;
  overallScore: number;
  detailAttempted: number;
  detailTotal: number;
  itemTotal: number;
}

export function RoadmapDetailHeader({
  topic,
  overallScore,
  detailAttempted,
  detailTotal,
  itemTotal,
}: RoadmapDetailHeaderProps) {
  const lvl = scoreLevel(overallScore);

  return (
    <div className="mb-7 flex items-start justify-between gap-8">
      {/* Left: topic */}
      <div className="min-w-0">
        <h1 className="text-2xl font-semibold tracking-tight">{topic}</h1>
      </div>

      {/* Right: score card */}
      <div className="grid min-w-[320px] shrink-0 grid-cols-[auto_1fr] items-center gap-[18px] rounded-lg border border-border bg-card p-[14px_18px]">
        <span
          className="font-mono text-[42px] font-semibold tabular-nums leading-none tracking-[-0.03em]"
          style={{ color: lvl.fg }}
        >
          {overallScore}
        </span>
        <div className="flex min-w-0 flex-col gap-2">
          <span className="text-[11px] font-medium uppercase tracking-[0.08em] text-muted-foreground">
            全体スコア
          </span>
          <ScoreBadge score={overallScore} />
          {/* Progress bar */}
          <div className="h-2 overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full transition-[width] duration-150 ease-out"
              style={{
                width: `${overallScore}%`,
                backgroundColor: lvl.fg,
              }}
            />
          </div>
          {/* Stats */}
          <div className="flex gap-3.5 whitespace-nowrap text-xs text-muted-foreground">
            <span>
              具体{" "}
              <span className="font-mono font-semibold tabular-nums text-foreground">
                {detailAttempted}
              </span>
              {" / "}
              <span className="font-mono font-semibold tabular-nums text-foreground">
                {detailTotal}
              </span>
              {" "}着手
            </span>
            <span>
              項目{" "}
              <span className="font-mono font-semibold tabular-nums text-foreground">
                {itemTotal}
              </span>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
