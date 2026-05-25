import { MessageSquare, Filter, AlertTriangle, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";

export function EmptyNoData() {
  return (
    <div className="mx-auto flex max-w-[480px] flex-col items-center px-6 pb-24 pt-[72px] text-center">
      <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-full border border-border bg-card">
        <MessageSquare className="h-9 w-9 text-muted-foreground" />
      </div>
      <div className="mb-1.5 text-base font-semibold tracking-tight">
        フィードバックはまだありません
      </div>
      <div className="text-[13px] leading-relaxed text-muted-foreground">
        Obsidianにノートを書くと、取り込み時にフィードバックが生成されます
      </div>
    </div>
  );
}

interface EmptyFilteredProps {
  onReset: () => void;
}

export function EmptyFiltered({ onReset }: EmptyFilteredProps) {
  return (
    <div className="mx-auto flex max-w-[480px] flex-col items-center px-6 pb-24 pt-[72px] text-center">
      <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-full border border-border bg-card">
        <Filter className="h-8 w-8 text-muted-foreground" />
      </div>
      <div className="mb-1.5 text-base font-semibold tracking-tight">
        条件に一致するフィードバックはありません
      </div>
      <div className="mb-6 text-[13px] leading-relaxed text-muted-foreground">
        フィルタ条件を変更するか、リセットしてすべて表示してください
      </div>
      <Button variant="ghost" size="sm" onClick={onReset}>
        <RotateCcw className="h-4 w-4" />
        リセット
      </Button>
    </div>
  );
}

interface FeedbackErrorProps {
  onRetry: () => void;
}

export function FeedbackError({ onRetry }: FeedbackErrorProps) {
  return (
    <div className="mx-auto flex max-w-[480px] flex-col items-center px-6 pb-24 pt-[72px] text-center">
      <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-full border border-rose-500/25 bg-rose-500/10">
        <AlertTriangle className="h-9 w-9 text-rose-400" />
      </div>
      <div className="mb-1.5 text-base font-semibold tracking-tight">
        フィードバックの読み込みに失敗しました
      </div>
      <div className="mb-6 text-[13px] leading-relaxed text-muted-foreground">
        ネットワーク接続を確認するか、少し待ってからもう一度お試しください
      </div>
      <Button onClick={onRetry}>
        <RotateCcw className="h-4 w-4" />
        再読み込み
      </Button>
    </div>
  );
}
