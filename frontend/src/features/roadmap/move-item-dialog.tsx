import { useState } from "react";
import { ArrowRightLeft, Folder, List } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useMoveItem } from "./use-roadmap-items";
import type { RoadmapTreeNode } from "@/types/api";

interface MoveItemDialogProps {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  node: RoadmapTreeNode | null;
  tree: RoadmapTreeNode[];
  roadmapId: string;
  onError?: (message: string) => void;
}

interface Candidate {
  id: string;
  label: string;
  level: "root" | "major" | "middle";
  disabled: boolean;
  isCurrent: boolean;
}

function buildCandidates(
  node: RoadmapTreeNode,
  tree: RoadmapTreeNode[],
): Candidate[] {
  const candidates: Candidate[] = [];

  if (node.level === "major") {
    candidates.push({
      id: "__root__",
      label: "ロードマップ直下（並び替え）",
      level: "root",
      disabled: false,
      isCurrent: false,
    });
  } else if (node.level === "middle") {
    for (const m of tree) {
      candidates.push({
        id: m.id,
        label: m.title,
        level: "major",
        disabled: false,
        isCurrent: m.children.some((c) => c.id === node.id),
      });
    }
  } else {
    for (const m of tree) {
      candidates.push({
        id: m.id,
        label: m.title,
        level: "major",
        disabled: true,
        isCurrent: false,
      });
      for (const mid of m.children) {
        candidates.push({
          id: mid.id,
          label: mid.title,
          level: "middle",
          disabled: false,
          isCurrent: mid.children.some((c) => c.id === node.id),
        });
      }
    }
  }

  return candidates;
}

export function MoveItemDialog({
  open,
  onOpenChange,
  node,
  tree,
  roadmapId,
  onError,
}: MoveItemDialogProps) {
  const [selectedParentId, setSelectedParentId] = useState<string | null>(null);
  const moveItem = useMoveItem(roadmapId);

  if (!node) return null;

  const candidates = buildCandidates(node, tree);

  const handleMove = () => {
    if (!selectedParentId) return;
    const parentId = selectedParentId === "__root__" ? null : selectedParentId;
    // Calculate target_order: append to end of target parent's children
    const findNode = (nodes: RoadmapTreeNode[], id: string): RoadmapTreeNode | undefined => {
      for (const n of nodes) {
        if (n.id === id) return n;
        const found = findNode(n.children ?? [], id);
        if (found) return found;
      }
      return undefined;
    };
    const targetOrder = parentId === null
      ? tree.length
      : (findNode(tree, parentId)?.children?.length ?? 0);
    moveItem.mutate(
      {
        itemId: node.id,
        targetParentId: parentId,
        targetOrder,
      },
      {
        onSuccess: () => onOpenChange(false),
        onError: () => {
          onOpenChange(false);
          onError?.("移動に失敗しました");
        },
      },
    );
  };

  const paddingClass = (level: string) => {
    if (level === "middle") return "pl-7";
    return "pl-2";
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[520px]">
        <DialogHeader>
          <DialogTitle>項目を移動</DialogTitle>
          <DialogDescription>
            <span className="font-semibold text-foreground">{node.title}</span>{" "}
            の移動先を選択してください。移動先の末尾に配置されます。
          </DialogDescription>
        </DialogHeader>

        <div>
          <label className="mb-1.5 block text-xs font-medium text-muted-foreground">
            移動先
          </label>
          <div className="max-h-[280px] overflow-y-auto rounded-md border border-border bg-background p-1.5">
            {candidates.map((c) => (
              <button
                key={c.id}
                type="button"
                disabled={c.disabled || c.isCurrent}
                className={`flex w-full items-center gap-2 rounded px-2 py-1.5 text-left font-sans text-[13px] transition-colors duration-[120ms] ${paddingClass(c.level)} ${
                  c.disabled || c.isCurrent
                    ? "cursor-not-allowed opacity-45"
                    : "cursor-pointer hover:bg-[rgb(51_65_85/0.4)]"
                } ${
                  selectedParentId === c.id
                    ? "bg-[rgb(37_99_235/0.18)] shadow-[inset_2px_0_0_0_var(--primary)]"
                    : ""
                } ${c.isCurrent ? "italic text-muted-foreground" : "text-foreground"}`}
                onClick={() => {
                  if (!c.disabled && !c.isCurrent) setSelectedParentId(c.id);
                }}
              >
                {c.level === "root" ? (
                  <List className={`h-[13px] w-[13px] shrink-0 ${selectedParentId === c.id ? "text-primary" : "text-muted-foreground"}`} />
                ) : (
                  <Folder className={`h-[13px] w-[13px] shrink-0 ${selectedParentId === c.id ? "text-primary" : "text-muted-foreground"}`} />
                )}
                <span className="min-w-0 flex-1 truncate">
                  {c.label}
                  {c.isCurrent ? "（現在の親）" : ""}
                </span>
              </button>
            ))}
          </div>
        </div>

        <DialogFooter>
          <Button variant="ghost" onClick={() => onOpenChange(false)}>
            キャンセル
          </Button>
          <Button
            onClick={handleMove}
            disabled={!selectedParentId || moveItem.isPending}
          >
            <ArrowRightLeft className="h-4 w-4" />
            移動する
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
