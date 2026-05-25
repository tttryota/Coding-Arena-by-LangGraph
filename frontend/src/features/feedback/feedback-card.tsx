import { Clock, MapPin, ChevronRight, ChevronDown, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { FeedbackBody } from "./feedback-body";
import type { FeedbackListItem } from "@/types/api";
import { formatRelativeTime } from "@/lib/relative-time";

interface FeedbackCardProps {
  item: FeedbackListItem;
  expanded: boolean;
  onToggle: () => void;
  onMarkRead: () => void;
  onOpenRoadmap: () => void;
}

export function FeedbackCard({
  item,
  expanded,
  onToggle,
  onMarkRead,
  onOpenRoadmap,
}: FeedbackCardProps) {
  const isRead = item.is_read;

  return (
    <div
      className={`flex flex-col gap-2.5 rounded-lg border border-border bg-card px-5 py-[18px] transition-[background,border-color,opacity] duration-150 ${
        isRead ? "opacity-70 hover:opacity-95" : ""
      } hover:border-[rgb(71_85_105/0.9)] hover:bg-[rgb(51_65_85/0.18)]`}
    >
      {/* Head row */}
      <div className="flex items-start gap-2.5">
        {/* Unread dot */}
        {isRead ? (
          <span className="w-2 shrink-0" />
        ) : (
          <span
            className="mt-[7px] h-2 w-2 shrink-0 rounded-full bg-primary shadow-[0_0_0_3px_rgb(37_99_235/0.12)]"
            aria-label="未読"
          />
        )}

        {/* Title column */}
        <div className="flex min-w-0 flex-1 flex-col gap-1">
          <div
            className={`truncate text-[14.5px] leading-[1.45] tracking-[-0.005em] ${
              isRead
                ? "font-medium text-muted-foreground"
                : "font-semibold text-foreground"
            }`}
          >
            {item.title}
          </div>
          <div className="truncate font-mono text-[11.5px] tracking-[-0.005em] text-muted-foreground">
            {item.source_path}
          </div>
        </div>

        {/* Timestamp */}
        <span
          className="flex shrink-0 items-center gap-1 pt-[3px] font-mono text-[11.5px] tabular-nums text-muted-foreground"
          title={item.created_at}
        >
          <Clock className="h-[11px] w-[11px]" />
          {formatRelativeTime(item.created_at)}
        </span>
      </div>

      {/* Body — click to toggle */}
      <div
        className={`flex cursor-pointer flex-col pl-[18px] ${expanded ? "gap-2" : "gap-1"}`}
        onClick={onToggle}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            onToggle();
          }
        }}
      >
        <FeedbackBody body={item.body} expanded={expanded} isRead={isRead} />
      </div>

      {/* Footer */}
      <div className="flex flex-wrap items-center gap-2 pl-[18px] mt-0.5">
        {/* Related roadmap badge */}
        {item.roadmap_item_id && (
          <button
            type="button"
            onClick={onOpenRoadmap}
            className="inline-flex max-w-full cursor-pointer items-center gap-1.5 rounded-full border border-[rgb(99_102_241/0.25)] bg-[rgb(99_102_241/0.1)] px-2.5 py-1 text-[11.5px] font-medium text-[#a5b4fc] transition-[background,border-color,color] duration-150 hover:border-[rgb(99_102_241/0.45)] hover:bg-[rgb(99_102_241/0.18)] hover:text-[#c7d2fe]"
          >
            <MapPin className="h-3 w-3 shrink-0" />
            <span className="max-w-[280px] truncate">関連ロードマップ</span>
            <ChevronRight className="h-[11px] w-[11px] shrink-0" />
          </button>
        )}

        {/* Expand hint */}
        <button
          type="button"
          onClick={onToggle}
          className="inline-flex cursor-pointer items-center gap-1 border-0 bg-transparent p-0 font-inherit text-[11.5px] text-muted-foreground hover:text-foreground"
        >
          {expanded ? "折りたたむ" : "全文を表示"}
          <ChevronDown
            className={`h-[11px] w-[11px] transition-transform duration-150 ${expanded ? "rotate-180" : ""}`}
          />
        </button>

        {/* Spacer */}
        <span className="flex-1" />

        {/* Mark as read */}
        {!isRead && (
          <Button variant="ghost" size="sm" onClick={onMarkRead}>
            <Check className="h-3.5 w-3.5" />
            既読にする
          </Button>
        )}
      </div>
    </div>
  );
}
