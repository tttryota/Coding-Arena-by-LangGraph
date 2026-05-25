import { FileText, Clock, Play } from "lucide-react";
import { scoreLevel } from "@/lib/score";
import { ScoreBadge } from "@/components/common/score-badge";
import { Button } from "@/components/ui/button";
import { OverflowMenu } from "./overflow-menu";
import { formatRelativeTime } from "@/lib/relative-time";
import type { RoadmapTreeNode } from "@/types/api";

interface DetailNodeProps {
  node: RoadmapTreeNode;
  onStartQuiz: (node: RoadmapTreeNode) => void;
  onDelete: (node: RoadmapTreeNode) => void;
  onMove: (node: RoadmapTreeNode) => void;
  isStartingQuiz?: boolean;
}

export function DetailNode({
  node,
  onStartQuiz,
  onDelete,
  onMove,
  isStartingQuiz,
}: DetailNodeProps) {
  const relTime = formatRelativeTime(node.last_quiz_at);
  const lvl = scoreLevel(node.score);

  return (
    <div className="flex cursor-default items-center gap-2.5 rounded-md px-2.5 py-[9px] transition-colors duration-[120ms] hover:bg-[rgb(51_65_85/0.32)]">
      <FileText className="h-3.5 w-3.5 shrink-0 text-slate-500" />

      {/* Body: title + description */}
      <div className="grid min-w-0 flex-1 gap-0.5">
        <div className="truncate text-[13.5px] font-medium text-foreground">
          {node.title}
        </div>
        <div className="truncate text-xs leading-relaxed text-muted-foreground">
          {node.description}
        </div>
      </div>

      {/* Meta: score + time + quiz btn + menu */}
      <div className="flex shrink-0 items-center gap-3.5">
        <span
          className="inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium leading-snug"
          style={{ color: lvl.fg, backgroundColor: lvl.bg }}
        >
          <span className="font-mono font-semibold tabular-nums">
            {node.score}
          </span>
        </span>
        <ScoreBadge score={node.score} />

        <span
          className={`inline-flex items-center justify-end gap-[5px] whitespace-nowrap font-mono text-[11px] tabular-nums text-muted-foreground ${
            !node.last_quiz_at ? "opacity-45" : ""
          }`}
          style={{ minWidth: 72 }}
        >
          <Clock className="h-[11px] w-[11px]" />
          <span>{relTime}</span>
        </span>

        <Button
          size="sm"
          className="h-7 gap-[5px] rounded-[5px] px-3 text-xs"
          onClick={() => onStartQuiz(node)}
          disabled={isStartingQuiz}
        >
          {isStartingQuiz ? (
            <>
              <span className="inline-block h-3 w-3 animate-[qs-spin_0.7s_linear_infinite] rounded-full border-[1.5px] border-[rgb(255_255_255/0.3)] border-t-white" />
              生成中…
            </>
          ) : (
            <>
              <Play className="h-3 w-3" />
              クイズ開始
            </>
          )}
        </Button>

        <OverflowMenu
          onMove={() => onMove(node)}
          onDelete={() => onDelete(node)}
        />
      </div>
    </div>
  );
}
