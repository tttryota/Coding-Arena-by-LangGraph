import { FolderPlus, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";

interface DetailEmptyStateProps {
  onAdd: () => void;
}

export function DetailEmptyState({ onAdd }: DetailEmptyStateProps) {
  return (
    <div className="rounded-lg border border-border bg-card p-2">
      <div className="flex flex-col items-center px-6 pb-16 pt-14 text-center text-muted-foreground">
        <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full border border-border bg-[rgb(51_65_85/0.4)]">
          <FolderPlus className="h-6 w-6 text-slate-500" />
        </div>
        <div className="mb-1 text-sm font-semibold text-foreground">
          まだ項目がありません
        </div>
        <div className="mb-5 max-w-[360px] text-xs leading-relaxed">
          大枠を追加してロードマップを組み立てましょう。AIにノートから生成させることもできます。
        </div>
        <Button onClick={onAdd}>
          <Plus className="h-4 w-4" />
          大枠を追加
        </Button>
      </div>
    </div>
  );
}
