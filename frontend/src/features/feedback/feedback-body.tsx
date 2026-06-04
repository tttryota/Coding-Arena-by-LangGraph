import { useMemo } from "react";

import { parseFeedbackBody } from "./feedback-body-parser";

interface FeedbackBodyProps {
  body: string
  expanded: boolean
  isRead: boolean
}

export function FeedbackBody({ body, expanded, isRead }: FeedbackBodyProps) {
  const sections = useMemo(() => parseFeedbackBody(body), [body])
  const mutedText = isRead ? "text-muted-foreground" : "text-foreground"

  if (!expanded) {
    const preview = sections.accuracy
      ? { label: "正確性チェック", text: sections.accuracy }
      : sections.suggestions.length
        ? { label: "改善提案", text: sections.suggestions[0] }
        : null;

    return (
      <>
        {sections.roadmap && (
          <div className="inline-flex items-baseline gap-1.5 min-w-0">
            <span className="shrink-0 text-[11px] font-medium uppercase tracking-[0.06em] text-muted-foreground">
              反映先ロードマップ
            </span>
            <span className={`min-w-0 truncate font-semibold ${mutedText}`}>
              {sections.roadmap}
            </span>
          </div>
        )}
        {preview && (
          <div className="flex items-baseline gap-2 text-[13px] leading-[1.55] min-w-0">
            <span className="shrink-0 text-[11px] font-medium uppercase tracking-[0.06em] text-muted-foreground">
              {preview.label}
            </span>
            <span
              className={`min-w-0 flex-1 line-clamp-2 ${mutedText}`}
            >
              {preview.text}
            </span>
          </div>
        )}
      </>
    );
  }

  return (
    <>
      {sections.roadmap && (
        <div className="inline-flex items-baseline gap-1.5 flex-wrap">
          <span className="text-[11px] font-medium uppercase tracking-[0.06em] text-muted-foreground">
            反映先ロードマップ
          </span>
          <span className={`font-semibold ${mutedText}`}>
            {sections.roadmap}
          </span>
        </div>
      )}
      {sections.accuracy && (
        <div className="flex flex-col gap-1">
          <span className="text-[11px] font-medium uppercase tracking-[0.06em] text-muted-foreground">
            正確性チェック
          </span>
          <span className={`text-[13px] leading-[1.6] ${mutedText}`}>
            {sections.accuracy}
          </span>
        </div>
      )}
      {sections.suggestions.length > 0 && (
        <div className="flex flex-col gap-1">
          <span className="text-[11px] font-medium uppercase tracking-[0.06em] text-muted-foreground">
            改善提案
          </span>
          <ul className="m-0 flex list-none flex-col gap-1 p-0">
            {sections.suggestions.map((s, i) => (
              <li
                key={i}
                className={`relative pl-4 text-[13px] leading-[1.6] ${mutedText} before:absolute before:left-1 before:top-[9px] before:h-1 before:w-1 before:rounded-full before:bg-muted-foreground`}
              >
                {s}
              </li>
            ))}
          </ul>
        </div>
      )}
    </>
  );
}
