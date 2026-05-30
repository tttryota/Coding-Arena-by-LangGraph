import { Dialog as DialogPrimitive } from "@base-ui/react/dialog";
import {
  Dialog,
  DialogPortal,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";

interface GeneratingDialogProps {
  open: boolean;
  /** 生成対象の名前（テーマ名、トピック名など） */
  target?: string;
  /** 追加の説明テキスト */
  description?: string;
}

export function GeneratingDialog({
  open,
  target,
  description,
}: GeneratingDialogProps) {
  return (
    <Dialog open={open}>
      <DialogPortal>
        {/* オーバーレイ: WCAG 対応で背景コンテンツを十分に遮る */}
        <DialogPrimitive.Backdrop
          className="fixed inset-0 z-50 bg-black/60 data-open:animate-in data-open:fade-in-0 data-closed:animate-out data-closed:fade-out-0"
        />
        <DialogPrimitive.Popup
          className="fixed top-1/2 left-1/2 z-50 w-full max-w-xs -translate-x-1/2 -translate-y-1/2 rounded-xl border border-border bg-card p-6 text-sm text-foreground shadow-lg outline-none data-open:animate-in data-open:fade-in-0 data-open:zoom-in-95 data-closed:animate-out data-closed:fade-out-0 data-closed:zoom-out-95"
        >
          <DialogHeader>
            <DialogTitle className="text-center">問題を生成中</DialogTitle>
            {target && (
              <DialogDescription className="text-center">
                <span className="font-medium text-foreground">{target}</span>
                {description && (
                  <>
                    <br />
                    {description}
                  </>
                )}
              </DialogDescription>
            )}
          </DialogHeader>
          <div className="flex justify-center py-6">
            <div className="relative h-10 w-10">
              <div className="absolute inset-0 animate-spin rounded-full border-2 border-primary/15 border-t-primary" />
            </div>
          </div>
          <p className="text-center text-xs text-muted-foreground">
            LLM が問題・採点基準を生成しています。しばらくお待ちください。
          </p>
        </DialogPrimitive.Popup>
      </DialogPortal>
    </Dialog>
  );
}
