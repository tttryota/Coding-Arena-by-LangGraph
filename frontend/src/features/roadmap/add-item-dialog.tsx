import { useState } from "react";
import { Plus } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useAddItem } from "./use-roadmap-items";
import type { RoadmapTreeNode } from "@/types/api";

interface AddItemDialogProps {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  parent: RoadmapTreeNode | null;
  roadmapId: string;
}

function childLevelLabel(parent: RoadmapTreeNode | null): string {
  if (!parent) return "大枠";
  if (parent.level === "major") return "中枠";
  return "具体";
}

export function AddItemDialog({
  open,
  onOpenChange,
  parent,
  roadmapId,
}: AddItemDialogProps) {
  const [title, setTitle] = useState("");
  const [desc, setDesc] = useState("");
  const [error, setError] = useState<string | null>(null);
  const addItem = useAddItem(roadmapId);
  const lvl = childLevelLabel(parent);

  const handleSubmit = () => {
    if (!title.trim()) {
      setError("タイトルを入力してください");
      return;
    }
    if (!desc.trim()) {
      setError("説明を入力してください");
      return;
    }
    addItem.mutate(
      {
        parent_id: parent?.id ?? null,
        title: title.trim(),
        description: desc.trim(),
      },
      {
        onSuccess: () => onOpenChange(false),
        onError: () => setError("追加に失敗しました。もう一度お試しください"),
      },
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[520px]">
        <DialogHeader>
          <DialogTitle>項目を追加</DialogTitle>
          <DialogDescription>
            {parent ? (
              <>
                追加先の親項目:{" "}
                <span className="font-semibold text-foreground">
                  {parent.title}
                </span>
                （{lvl}として追加されます）
              </>
            ) : (
              <>
                ロードマップ直下に
                <span className="font-semibold text-foreground">大枠</span>
                を追加します
              </>
            )}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3.5">
          <div>
            <label className="mb-1.5 block text-xs font-medium text-muted-foreground">
              タイトル
            </label>
            <Input
              value={title}
              onChange={(e) => {
                setTitle(e.target.value);
                if (error) setError(null);
              }}
              placeholder={`${lvl}のタイトル`}
            />
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-medium text-muted-foreground">
              説明
            </label>
            <Textarea
              value={desc}
              onChange={(e) => {
                setDesc(e.target.value);
                if (error) setError(null);
              }}
              placeholder="この項目で何を学ぶか、簡単に説明してください"
            />
          </div>
        </div>

        {error && (
          <p className="text-xs text-destructive">{error}</p>
        )}

        <DialogFooter>
          <Button variant="ghost" onClick={() => onOpenChange(false)}>
            キャンセル
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={addItem.isPending}
          >
            <Plus className="h-4 w-4" />
            追加
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
