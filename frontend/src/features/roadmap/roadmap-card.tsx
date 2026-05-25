import { scoreLevel } from "@/lib/score";
import { ScoreBadge } from "@/components/common/score-badge";
import type { RoadmapListItem } from "@/types/api";

interface RoadmapCardProps {
  roadmap: RoadmapListItem;
  onClick: () => void;
}

export function RoadmapCard({ roadmap, onClick }: RoadmapCardProps) {
  const lvl = scoreLevel(roadmap.overall_score);

  return (
    <button
      type="button"
      onClick={onClick}
      className="flex cursor-pointer flex-col rounded-lg border border-border bg-card p-5 text-left transition-colors duration-150 hover:border-[rgb(71_85_105/0.9)] hover:bg-[rgb(51_65_85/0.25)]"
    >
      {/* Header: topic + badge */}
      <div className="mb-3.5 flex items-start justify-between gap-3">
        <span className="text-[15px] font-semibold leading-snug tracking-tight text-foreground">
          {roadmap.topic}
        </span>
        <ScoreBadge score={roadmap.overall_score} />
      </div>

      {/* Score row */}
      <div className="flex items-center gap-3.5">
        <span
          className="font-mono text-[26px] font-semibold leading-none tabular-nums"
          style={{ color: lvl.fg }}
        >
          {roadmap.overall_score}
        </span>
        <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
          <div
            className="h-full rounded-full transition-[width] duration-150 ease-out"
            style={{
              width: `${roadmap.overall_score}%`,
              backgroundColor: lvl.fg,
            }}
          />
        </div>
      </div>
    </button>
  );
}
