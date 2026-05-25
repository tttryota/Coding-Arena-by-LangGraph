import { FileText, RotateCcw } from "lucide-react";
import type { SessionState } from "@/types/api";

interface SessionHeaderProps {
  sessionState: SessionState;
}

export function SessionHeader({ sessionState: s }: SessionHeaderProps) {
  const cpCount = s.confirmation_points?.length ?? 0;

  return (
    <div className="mb-5">
      {/* Meta row */}
      <div className="mb-1.5 flex items-center gap-2.5 text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-1 rounded-full border border-[rgb(59_130_246/0.2)] bg-[rgb(59_130_246/0.08)] px-[7px] py-px text-[11px] tracking-wide text-[#60a5fa]">
          <FileText className="h-[11px] w-[11px]" />
          具体項目
        </span>
        <span>
          確認ポイント{" "}
          <b className="font-semibold text-foreground">{cpCount}</b> 件
        </span>
        <span className="opacity-50">&middot;</span>
        <span>
          セッション{" "}
          <span className="font-mono">{s.session_id}</span>
        </span>
        {s.is_resumed && (
          <>
            <span className="opacity-50">&middot;</span>
            <span className="inline-flex items-center gap-1 text-[#60a5fa]">
              <RotateCcw className="h-[11px] w-[11px]" />
              再開
            </span>
          </>
        )}
      </div>

      {/* Title */}
      <div className="mb-1 text-lg font-semibold leading-snug tracking-tight text-foreground">
        {s.roadmap_item_title}
      </div>

      {/* Description */}
      <div className="max-w-[680px] text-[13px] leading-relaxed text-muted-foreground">
        {s.roadmap_item_description}
      </div>
    </div>
  );
}
