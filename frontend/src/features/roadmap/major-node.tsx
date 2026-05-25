import { ChevronRight, Folder, FolderOpen, Plus } from "lucide-react";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { ScoreBadge } from "@/components/common/score-badge";
import { Button } from "@/components/ui/button";
import { scoreLevel } from "@/lib/score";
import { MiniProgress } from "./mini-progress";
import { OverflowMenu } from "./overflow-menu";
import { MiddleNode } from "./middle-node";
import { useTreeStore } from "./use-tree-store";
import type { RoadmapTreeNode } from "@/types/api";

interface MajorNodeProps {
  node: RoadmapTreeNode;
  isFirst: boolean;
  onStartQuiz: (node: RoadmapTreeNode) => void;
  onAddChild: (parent: RoadmapTreeNode) => void;
  onDelete: (node: RoadmapTreeNode) => void;
  onMove: (node: RoadmapTreeNode) => void;
}

export function MajorNode({
  node,
  isFirst,
  onStartQuiz,
  onAddChild,
  onDelete,
  onMove,
}: MajorNodeProps) {
  const expanded = useTreeStore((s) => s.expandedIds.has(node.id));
  const toggle = useTreeStore((s) => s.toggle);
  const lvl = scoreLevel(node.score);
  const FolderIcon = expanded ? FolderOpen : Folder;

  return (
    <Collapsible open={expanded} onOpenChange={() => toggle(node.id)}>
      <div
        className={`py-0.5 ${!isFirst ? "mt-1 border-t border-border pt-1.5" : ""}`}
      >
        <CollapsibleTrigger asChild>
          <div
            className="flex cursor-pointer items-center gap-2.5 rounded-md p-3 transition-colors duration-[120ms] hover:bg-[rgb(51_65_85/0.32)]"
            role="button"
            aria-expanded={expanded}
          >
            <ChevronRight
              className={`h-4 w-4 shrink-0 text-muted-foreground transition-transform duration-150 ease-out ${
                expanded ? "rotate-90" : ""
              }`}
            />

            {/* Score color stripe */}
            <span
              className="w-[3px] shrink-0 self-stretch rounded-full opacity-85"
              style={{ backgroundColor: lvl.fg }}
            />

            <FolderIcon className="h-4 w-4 shrink-0 text-slate-300" />
            <span className="min-w-0 flex-1 text-[15px] font-semibold tracking-[-0.005em]">
              {node.title}
            </span>

            {/* Meta */}
            <div className="flex shrink-0 items-center gap-3 font-mono tabular-nums text-xs text-muted-foreground">
              <MiniProgress value={node.score} width={72} />
              <span
                className="min-w-[24px] text-right text-[13px] font-semibold tracking-[-0.01em]"
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
                aria-label="子を追加"
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
            <div className="ml-4 border-l border-border">
              {node.children.map((child) => (
                <MiddleNode
                  key={child.id}
                  node={child}
                  onStartQuiz={onStartQuiz}
                  onAddChild={onAddChild}
                  onDelete={onDelete}
                  onMove={onMove}
                />
              ))}
            </div>
          )}
        </CollapsibleContent>
      </div>
    </Collapsible>
  );
}
