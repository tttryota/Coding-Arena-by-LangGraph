import { ChevronsDown, ChevronsUp } from "lucide-react";
import { MajorNode } from "./major-node";
import { useTreeStore } from "./use-tree-store";
import type { RoadmapTreeNode } from "@/types/api";

interface RoadmapTreeProps {
  items: RoadmapTreeNode[];
  detailCount: number;
  onStartQuiz: (node: RoadmapTreeNode) => void;
  onAddChild: (parent: RoadmapTreeNode) => void;
  onDelete: (node: RoadmapTreeNode) => void;
  onMove: (node: RoadmapTreeNode) => void;
}

function collectAllIds(nodes: RoadmapTreeNode[]): string[] {
  const ids: string[] = [];
  const walk = (arr: RoadmapTreeNode[]) => {
    for (const n of arr) {
      ids.push(n.id);
      if (n.children?.length) walk(n.children);
    }
  };
  walk(nodes);
  return ids;
}

export function RoadmapTree({
  items,
  detailCount,
  onStartQuiz,
  onAddChild,
  onDelete,
  onMove,
}: RoadmapTreeProps) {
  const expandAll = useTreeStore((s) => s.expandAll);
  const collapseAll = useTreeStore((s) => s.collapseAll);

  const handleExpandAll = () => expandAll(collectAllIds(items));
  const handleCollapseAll = () => collapseAll();

  return (
    <div className="rounded-lg border border-border bg-card p-2">
      {/* Toolbar */}
      <div className="mb-1.5 flex items-center justify-between border-b border-border px-3 pb-3 pt-2">
        <div className="flex gap-1.5">
          <button
            type="button"
            className="inline-flex cursor-pointer items-center gap-[5px] rounded bg-transparent px-2 py-1 font-sans text-xs text-muted-foreground transition-colors duration-[120ms] hover:bg-[rgb(51_65_85/0.4)] hover:text-foreground"
            onClick={handleExpandAll}
          >
            <ChevronsDown className="h-3 w-3" />
            全て展開
          </button>
          <button
            type="button"
            className="inline-flex cursor-pointer items-center gap-[5px] rounded bg-transparent px-2 py-1 font-sans text-xs text-muted-foreground transition-colors duration-[120ms] hover:bg-[rgb(51_65_85/0.4)] hover:text-foreground"
            onClick={handleCollapseAll}
          >
            <ChevronsUp className="h-3 w-3" />
            全て折畳
          </button>
        </div>
        <span className="font-mono text-xs tabular-nums text-muted-foreground">
          {detailCount} 具体項目
        </span>
      </div>

      {/* Tree nodes */}
      {items.map((node, i) => (
        <MajorNode
          key={node.id}
          node={node}
          isFirst={i === 0}
          onStartQuiz={onStartQuiz}
          onAddChild={onAddChild}
          onDelete={onDelete}
          onMove={onMove}
        />
      ))}
    </div>
  );
}
