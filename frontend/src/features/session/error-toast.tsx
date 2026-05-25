import { AlertTriangle, X } from "lucide-react";

interface ErrorToastProps {
  onClose: () => void;
}

export function ErrorToast({ onClose }: ErrorToastProps) {
  return (
    <div
      role="alert"
      className="fixed bottom-6 left-1/2 z-40 flex min-w-[320px] -translate-x-1/2 animate-[toast-in_200ms_ease-out] items-center gap-3 rounded-lg border border-[rgb(244_63_94/0.4)] border-l-[3px] border-l-[#fb7185] bg-card px-4 py-3 text-[13px] text-foreground shadow-[0_12px_32px_-8px_rgb(0_0_0/0.6)]"
    >
      <AlertTriangle className="h-4 w-4 shrink-0 text-[#fb7185]" />
      <div className="flex-1">
        <div className="font-medium">接続エラーが発生しました</div>
        <div className="mt-0.5 text-xs text-muted-foreground">
          もう一度お試しください。入力内容は保持されています。
        </div>
      </div>
      <button
        type="button"
        className="inline-flex cursor-pointer items-center p-1 text-muted-foreground hover:text-foreground"
        onClick={onClose}
        aria-label="閉じる"
      >
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}
