import { useNavigate } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import { ScoreBadge } from "@/components/common/score-badge";
import { MiniProgress } from "@/features/roadmap/mini-progress";
import type { RoadmapListItem } from "@/types/api";

interface RoadmapSummaryProps {
  roadmaps: RoadmapListItem[];
  totalCount: number;
}

export function RoadmapSummary({ roadmaps, totalCount }: RoadmapSummaryProps) {
  const navigate = useNavigate();

  if (roadmaps.length === 0) {
    return (
      <div className="flex flex-col overflow-hidden rounded-lg border border-border bg-card">
        <div className="flex items-center justify-between border-b border-border px-[18px] py-3.5">
          <span className="text-[13px] font-semibold tracking-[-0.005em]">
            ロードマップ
          </span>
        </div>
        <div className="flex flex-col items-center gap-2 px-6 py-10 text-center">
          <span className="text-sm text-muted-foreground">
            ロードマップがありません
          </span>
          <button
            type="button"
            className="cursor-pointer text-sm text-primary hover:underline"
            onClick={() => navigate("/roadmaps")}
          >
            作成する
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col overflow-hidden rounded-lg border border-border bg-card">
      {/* Header */}
      <div className="flex items-baseline gap-2.5 border-b border-border px-[18px] py-3.5">
        <span className="text-[13px] font-semibold tracking-[-0.005em]">
          ロードマップ
        </span>
        {totalCount > roadmaps.length && (
          <span className="font-mono text-[11px] tabular-nums text-muted-foreground">
            {roadmaps.length} / {totalCount}
          </span>
        )}
      </div>

      {/* Rows */}
      <div className="flex flex-col gap-0.5 p-1.5">
        {roadmaps.map((r) => (
          <button
            key={r.roadmap_id}
            type="button"
            className="group grid w-full cursor-pointer grid-cols-[minmax(0,1fr)_130px_auto_14px] items-center gap-3 rounded-[6px] border-0 bg-transparent px-3 py-2.5 text-left font-inherit text-foreground transition-[background] duration-150 hover:bg-[rgb(51_65_85/0.4)] focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-ring"
            onClick={() => navigate(`/roadmaps/${r.roadmap_id}`)}
          >
            <span className="truncate text-sm font-medium">{r.topic}</span>
            <MiniProgress value={r.overall_score} width={130} />
            <ScoreBadge score={r.overall_score} variant="numeral" />
            <ChevronRight
              size={14}
              className="text-muted-foreground opacity-70 transition-opacity group-hover:opacity-100 group-hover:text-foreground"
            />
          </button>
        ))}
      </div>

      {/* Footer */}
      {totalCount > roadmaps.length && (
        <div className="flex items-center justify-end border-t border-border px-3.5 py-2">
          <button
            type="button"
            className="inline-flex cursor-pointer items-center gap-0.5 rounded px-1.5 py-1 text-xs text-muted-foreground transition-[color,background] duration-150 hover:bg-[rgb(51_65_85/0.4)] hover:text-foreground"
            onClick={() => navigate("/roadmaps")}
          >
            すべて見る
            <ChevronRight size={12} />
          </button>
        </div>
      )}
    </div>
  );
}
