import { RotateCcw } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import type { RoadmapTreeNode } from "@/types/api";

interface ResumeSessionDialogProps {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  node: RoadmapTreeNode | null;
  onResume: () => void;
}

export function ResumeSessionDialog({
  open,
  onOpenChange,
  node,
  onResume,
}: ResumeSessionDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[460px]">
        <DialogHeader>
          <DialogTitle>進行中のセッションがあります</DialogTitle>
          <DialogDescription>
            この項目には進行中のクイズセッションがあります。前回の続きから再開しますか？
          </DialogDescription>
        </DialogHeader>

        <div className="rounded-md border border-border bg-background px-3 py-2.5 font-mono text-xs tabular-nums text-muted-foreground">
          項目: <span className="font-semibold text-foreground">{node?.title ?? "—"}</span>
        </div>

        <DialogFooter>
          <Button variant="ghost" onClick={() => onOpenChange(false)}>
            キャンセル
          </Button>
          <Button onClick={onResume}>
            <RotateCcw className="h-4 w-4" />
            再開する
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
