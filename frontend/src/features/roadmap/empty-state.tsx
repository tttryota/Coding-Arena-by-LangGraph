import { Map, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";

interface EmptyStateProps {
  onCreate: () => void;
}

export function EmptyState({ onCreate }: EmptyStateProps) {
  return (
    <div className="mx-auto flex max-w-[480px] flex-col items-center px-6 pb-24 pt-[72px] text-center">
      <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-full border border-border bg-[rgb(51_65_85/0.4)]">
        <Map className="h-9 w-9 text-muted-foreground" />
      </div>
      <div className="mb-1.5 text-base font-semibold tracking-tight">
        ロードマップがまだありません
      </div>
      <div className="mb-6 text-[13px] leading-relaxed text-muted-foreground">
        学習したいトピックを入力すると、AIがロードマップを生成します
      </div>
      <Button onClick={onCreate}>
        <Plus className="h-4 w-4" />
        新規作成
      </Button>
    </div>
  );
}
