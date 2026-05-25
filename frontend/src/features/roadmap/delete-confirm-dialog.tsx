import { Trash2, AlertTriangle } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useDeleteItem } from "./use-roadmap-items";
import type { RoadmapTreeNode } from "@/types/api";

interface DeleteConfirmDialogProps {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  node: RoadmapTreeNode | null;
  roadmapId: string;
  onError?: (message: string) => void;
}

function countDescendants(node: RoadmapTreeNode | null): number {
  if (!node) return 0;
  let n = 0;
  const walk = (arr: RoadmapTreeNode[]) => {
    for (const c of arr) {
      n++;
      walk(c.children ?? []);
    }
  };
  walk(node.children ?? []);
  return n;
}

export function DeleteConfirmDialog({
  open,
  onOpenChange,
  node,
  roadmapId,
  onError,
}: DeleteConfirmDialogProps) {
  const deleteItem = useDeleteItem(roadmapId);
  const childrenCount = countDescendants(node);

  const handleDelete = () => {
    if (!node) return;
    deleteItem.mutate(node.id, {
      onSuccess: () => onOpenChange(false),
      onError: () => {
        onOpenChange(false);
        onError?.("削除に失敗しました");
      },
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[440px]">
        <DialogHeader>
          <DialogTitle>項目を削除</DialogTitle>
          <DialogDescription>
            <span className="font-semibold text-foreground">
              {node?.title}
            </span>{" "}
            を削除しますか？子項目も全て削除されます。この操作は取り消せません。
          </DialogDescription>
        </DialogHeader>

        {childrenCount > 0 && (
          <div className="flex gap-2 rounded-md border border-rose-500/25 bg-rose-500/[0.08] px-3 py-2.5 text-xs leading-relaxed text-score-insufficient-fg">
            <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            <span>
              子項目 <span className="font-semibold">{childrenCount}</span>{" "}
              件も同時に削除されます。
            </span>
          </div>
        )}

        <DialogFooter>
          <Button variant="ghost" onClick={() => onOpenChange(false)}>
            キャンセル
          </Button>
          <Button
            variant="destructive"
            onClick={handleDelete}
            disabled={deleteItem.isPending}
          >
            <Trash2 className="h-4 w-4" />
            削除する
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
