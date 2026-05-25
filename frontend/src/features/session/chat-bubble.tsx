import { Sparkles } from "lucide-react";

interface ChatBubbleProps {
  text: string;
}

export function ChatBubble({ text }: ChatBubbleProps) {
  return (
    <div className="mb-3.5 flex animate-[bubble-in_180ms_ease-out] gap-3 rounded-lg border border-border bg-[rgb(2_6_23/0.5)] p-3.5 pt-3.5">
      <span className="inline-flex h-[26px] w-[26px] shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-[#3b82f6] to-[#6366f1]">
        <Sparkles className="h-[13px] w-[13px] text-white" />
      </span>
      <div className="min-w-0 flex-1">
        <div className="mb-1 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
          アシスタント
        </div>
        <div className="whitespace-pre-wrap text-[13px] leading-relaxed text-foreground">
          {text}
        </div>
      </div>
    </div>
  );
}
