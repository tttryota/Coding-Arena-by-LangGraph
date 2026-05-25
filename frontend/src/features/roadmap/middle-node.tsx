import { ChevronRight, Folder, FolderOpen, Plus } from "lucide-react";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { ScoreBadge } from "@/components/common/score-badge";
import { Button } from "@/components/ui/button";
import { scoreLevel } from "@/lib/score";
import { MiniProgress } from "./mini-progress";
import { OverflowMenu } from "./overflow-menu";
import { DetailNode } from "./detail-node";
import { useTreeStore } from "./use-tree-store";
import type { RoadmapTreeNode } from "@/types/api";

interface MiddleNodeProps {
  node: RoadmapTreeNode;
  onStartQuiz: (node: RoadmapTreeNode) => void;
  onAddChild: (parent: RoadmapTreeNode) => void;
  onDelete: (node: RoadmapTreeNode) => void;
  onMove: (node: RoadmapTreeNode) => void;
  isStartingQuiz?: boolean;
}

export function MiddleNode({
  node,
  onStartQuiz,
  onAddChild,
  onDelete,
  onMove,
  isStartingQuiz,
}: MiddleNodeProps) {
  const expanded = useTreeStore((s) => s.expandedIds.has(node.id));
  const toggle = useTreeStore((s) => s.toggle);
  const lvl = scoreLevel(node.score);
  const childCount = node.children?.length || 0;
  const FolderIcon = expanded ? FolderOpen : Folder;

  return (
    <Collapsible open={expanded} onOpenChange={() => toggle(node.id)}>
      <div className="tn-middle-block">
        <CollapsibleTrigger>
          <div
            className="flex cursor-pointer items-center gap-2.5 rounded-md px-2.5 py-[9px] transition-colors duration-[120ms] hover:bg-[rgb(51_65_85/0.32)]"
            role="button"
            aria-expanded={expanded}
          >
            <ChevronRight
              className={`h-3.5 w-3.5 shrink-0 text-muted-foreground transition-transform duration-150 ease-out ${
                expanded ? "rotate-90" : ""
              }`}
            />
            <FolderIcon className="h-3.5 w-3.5 shrink-0 text-slate-400" />
            <span className="min-w-0 flex-1 text-sm font-medium text-foreground">
              {node.title}
            </span>

            {/* Meta */}
            <div className="flex shrink-0 items-center gap-2.5 text-xs text-muted-foreground">
              <span className="whitespace-nowrap font-mono tabular-nums">
                {childCount} 項目
              </span>
              <MiniProgress value={node.score} width={48} />
              <span
                className="min-w-[24px] text-right font-mono text-[13px] font-semibold tabular-nums"
                style={{ color: lvl.fg }}
              >
                {node.score}
              </span>
              <ScoreBadge score={node.score} />
            </div>

            {/* Actions */}
            <span onClick={(e) => e.stopPropagation()}>
              <Button
                variant="ghost"
                size="sm"
                className="h-7 w-7 p-0"
                aria-label="具体項目を追加"
                onClick={() => onAddChild(node)}
              >
                <Plus className="h-3.5 w-3.5" />
              </Button>
            </span>
            <OverflowMenu
              onMove={() => onMove(node)}
              onDelete={() => onDelete(node)}
            />
          </div>
        </CollapsibleTrigger>

        <CollapsibleContent>
          {node.children?.length > 0 && (
            <div className="ml-8 border-l border-border">
              {node.children.map((child) => (
                <DetailNode
                  key={child.id}
                  node={child}
                  onStartQuiz={onStartQuiz}
                  onDelete={onDelete}
                  onMove={onMove}
                  isStartingQuiz={isStartingQuiz}
                />
              ))}
            </div>
          )}
        </CollapsibleContent>
      </div>
    </Collapsible>
  );
}
