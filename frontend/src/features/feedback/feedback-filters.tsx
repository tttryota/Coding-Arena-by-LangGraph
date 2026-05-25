import { Calendar, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";

interface FeedbackFiltersProps {
  dateFrom: string | null;
  dateTo: string | null;
  readStatus: "all" | "unread" | "read";
  onDateFromChange: (v: string | null) => void;
  onDateToChange: (v: string | null) => void;
  onReadStatusChange: (v: "all" | "unread" | "read") => void;
  onReset: () => void;
  isDirty: boolean;
}

export function FeedbackFilters({
  dateFrom,
  dateTo,
  readStatus,
  onDateFromChange,
  onDateToChange,
  onReadStatusChange,
  onReset,
  isDirty,
}: FeedbackFiltersProps) {
  return (
    <div className="mb-4 flex flex-wrap items-center gap-4 rounded-lg border border-border bg-card px-4 py-3">
      {/* Date range */}
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <Calendar className="h-3.5 w-3.5" />
        <span>期間</span>
        <input
          type="date"
          className="min-w-[140px] rounded-md border border-input bg-background px-2.5 py-1.5 font-inherit text-[13px] tabular-nums text-foreground outline-none transition-[border-color,box-shadow] duration-150 [color-scheme:dark] focus:border-ring focus:shadow-[0_0_0_2px_rgb(59_130_246/0.25)]"
          value={dateFrom ?? ""}
          onChange={(e) => onDateFromChange(e.target.value || null)}
          aria-label="開始日"
        />
        <span className="px-0.5 text-xs text-muted-foreground">〜</span>
        <input
          type="date"
          className="min-w-[140px] rounded-md border border-input bg-background px-2.5 py-1.5 font-inherit text-[13px] tabular-nums text-foreground outline-none transition-[border-color,box-shadow] duration-150 [color-scheme:dark] focus:border-ring focus:shadow-[0_0_0_2px_rgb(59_130_246/0.25)]"
          value={dateTo ?? ""}
          onChange={(e) => onDateToChange(e.target.value || null)}
          aria-label="終了日"
        />
      </div>

      {/* Read status */}
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <span>表示</span>
        <select
          className="cursor-pointer appearance-none rounded-md border border-input bg-background bg-[url('data:image/svg+xml;utf8,<svg%20xmlns=%22http://www.w3.org/2000/svg%22%20width=%2210%22%20height=%226%22%20viewBox=%220%200%2010%206%22><path%20fill=%22%2394a3b8%22%20d=%22M0%200h10L5%206z%22/></svg>')] bg-[position:right_10px_center] bg-no-repeat py-1.5 pl-2.5 pr-[30px] font-inherit text-[13px] text-foreground outline-none transition-[border-color,box-shadow] duration-150 focus:border-ring focus:shadow-[0_0_0_2px_rgb(59_130_246/0.25)]"
          value={readStatus}
          onChange={(e) =>
            onReadStatusChange(
              e.target.value as "all" | "unread" | "read",
            )
          }
          aria-label="表示フィルタ"
        >
          <option value="all">すべて</option>
          <option value="unread">未読のみ</option>
          <option value="read">既読のみ</option>
        </select>
      </div>

      {/* Spacer */}
      <span className="flex-1" />

      {/* Reset */}
      {isDirty && (
        <Button variant="ghost" size="sm" onClick={onReset}>
          <RotateCcw className="h-3.5 w-3.5" />
          リセット
        </Button>
      )}
    </div>
  );
}
