import { useNavigate } from "react-router-dom";
import { BookOpenText, MessageSquare, Swords, Database, Target } from "lucide-react";
import { ScoreBadge } from "@/components/common/score-badge";
import { formatRelativeTime } from "@/lib/relative-time";
import type { ActivityItem } from "./use-dashboard-data";

interface RecentActivityProps {
  activity: ActivityItem[];
}

export function RecentActivity({ activity }: RecentActivityProps) {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col overflow-hidden rounded-lg border border-border bg-card">
      {/* Header */}
      <div className="flex items-baseline gap-2.5 border-b border-border px-[18px] py-3.5">
        <span className="text-[13px] font-semibold tracking-[-0.005em]">
          最近のアクティビティ
        </span>
        {activity.length > 0 && (
          <span className="font-mono text-[11px] tabular-nums text-muted-foreground">
            {activity.length}
          </span>
        )}
      </div>

      {/* Rows */}
      <div className="flex flex-1 flex-col p-1.5">
        {activity.length === 0 && (
          <div className="flex items-center justify-center px-6 py-10 text-sm text-muted-foreground">
            まだアクティビティがありません
          </div>
        )}

        {activity.map((item, i) => {
          const isQuiz = item.kind === "quiz";
          const isCompetitive = item.kind === "competitive";
          const isAlgorithmFoundations = item.kind === "algorithm_foundations";
          const isSqlDojo = item.kind === "sql_dojo";
          const isFeedback = item.kind === "feedback";
          const time = isQuiz
            ? formatRelativeTime(item.lastQuizAt)
            : formatRelativeTime(item.createdAt);

          return (
            <button
              key={
                isQuiz
                  ? `q-${item.itemId}`
                  : isCompetitive
                    ? `c-${item.sessionId}`
                    : isAlgorithmFoundations
                      ? `a-${item.sessionId}`
                    : isSqlDojo
                      ? `s-${item.sessionId}`
                    : `f-${item.id}`
              }
              type="button"
              className={[
                "relative flex w-full cursor-pointer items-start gap-3 rounded-[6px] border-0 bg-transparent px-3 py-[11px] text-left font-inherit text-foreground transition-[background] duration-150 hover:bg-[rgb(51_65_85/0.4)] focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-ring",
                i > 0 && "shadow-[inset_0_1px_0_0_var(--border)]",
                isFeedback && item.unread && "is-unread",
              ]
                .filter(Boolean)
                .join(" ")}
              onClick={() => {
                if (isQuiz) {
                  navigate(`/roadmaps/${item.roadmapId}`);
                } else if (isCompetitive) {
                  navigate(`/algorithm-quiz/${item.sessionId}`);
                } else if (isAlgorithmFoundations) {
                  navigate(`/algorithm-foundations/${item.sessionId}`);
                } else if (isSqlDojo) {
                  navigate(`/sql-dojo/${item.sessionId}`);
                } else {
                  navigate("/feedbacks");
                }
              }}
            >
              {/* Unread left bar */}
              {isFeedback && item.unread && (
                <span className="absolute bottom-3 left-1 top-3 w-0.5 rounded-r bg-primary opacity-70" />
              )}

              {/* Icon */}
              <span
                className={[
                  "mt-px inline-flex h-[22px] w-[22px] shrink-0 items-center justify-center rounded-[6px] border",
                  isQuiz
                    ? "border-[rgb(59_130_246/0.25)] bg-[rgb(59_130_246/0.1)] text-[#93c5fd]"
                    : isCompetitive
                      ? "border-[rgb(234_179_8/0.25)] bg-[rgb(234_179_8/0.1)] text-[#fde047]"
                      : isAlgorithmFoundations
                        ? "border-[rgb(16_185_129/0.25)] bg-[rgb(16_185_129/0.1)] text-[#6ee7b7]"
                      : isSqlDojo
                        ? "border-[rgb(34_211_238/0.25)] bg-[rgb(34_211_238/0.1)] text-[#67e8f9]"
                      : "border-[rgb(168_85_247/0.22)] bg-[rgb(168_85_247/0.1)] text-[#c4b5fd]",
                ].join(" ")}
              >
                {isQuiz ? (
                  <BookOpenText size={13} />
                ) : isCompetitive ? (
                  <Swords size={13} />
                ) : isAlgorithmFoundations ? (
                  <Target size={13} />
                ) : isSqlDojo ? (
                  <Database size={13} />
                ) : (
                  <MessageSquare size={13} />
                )}
              </span>

              {/* Body */}
              <span className="flex min-w-0 flex-1 flex-col gap-1">
                <span className="truncate text-[13px] font-medium tracking-[-0.005em] text-foreground">
                  {isCompetitive
                    ? item.themeLabel
                    : isAlgorithmFoundations
                      ? item.unitTitle
                    : isSqlDojo
                      ? item.topicTitle ?? item.themeTitle
                      : item.title}
                </span>
                <span className="flex items-center gap-2 text-[11px] text-muted-foreground">
                  {isQuiz || isCompetitive || isAlgorithmFoundations || isSqlDojo ? (
                    <>
                      <ScoreBadge score={item.score} />
                      <span className="h-[3px] w-[3px] shrink-0 rounded-full bg-border" />
                      <span
                        className="shrink-0 whitespace-nowrap"
                        title={isQuiz ? item.lastQuizAt : item.createdAt}
                      >
                        {time}
                      </span>
                    </>
                  ) : item.kind === "feedback" ? (
                    <>
                      {item.unread && (
                        <span className="inline-flex shrink-0 items-center rounded-full border border-[rgb(59_130_246/0.35)] bg-[rgb(37_99_235/0.15)] px-[7px] py-px text-[10px] font-semibold tracking-[0.04em] text-[#93c5fd]">
                          未読
                        </span>
                      )}
                      <span className="h-[3px] w-[3px] shrink-0 rounded-full bg-border" />
                      <span
                        className="shrink-0 whitespace-nowrap"
                        title={item.createdAt}
                      >
                        {time}
                      </span>
                    </>
                  ) : null}
                </span>
              </span>
            </button>
          );
        })}
      </div>

      {/* Footer legend */}
      {activity.length > 0 && (
        <div className="flex items-center gap-3.5 border-t border-border px-3.5 py-2">
          <span className="inline-flex items-center gap-1.5 text-[11px] text-muted-foreground">
            <span className="inline-flex h-[18px] w-[18px] items-center justify-center rounded-[6px] border border-[rgb(59_130_246/0.25)] bg-[rgb(59_130_246/0.1)] text-[#93c5fd]">
              <BookOpenText size={11} />
            </span>
            クイズ結果
          </span>
          <span className="inline-flex items-center gap-1.5 text-[11px] text-muted-foreground">
            <span className="inline-flex h-[18px] w-[18px] items-center justify-center rounded-[6px] border border-[rgb(234_179_8/0.25)] bg-[rgb(234_179_8/0.1)] text-[#fde047]">
              <Swords size={11} />
            </span>
            競プロ
          </span>
          <span className="inline-flex items-center gap-1.5 text-[11px] text-muted-foreground">
            <span className="inline-flex h-[18px] w-[18px] items-center justify-center rounded-[6px] border border-[rgb(16_185_129/0.25)] bg-[rgb(16_185_129/0.1)] text-[#6ee7b7]">
              <Target size={11} />
            </span>
            競プロうさぎ
          </span>
          <span className="inline-flex items-center gap-1.5 text-[11px] text-muted-foreground">
            <span className="inline-flex h-[18px] w-[18px] items-center justify-center rounded-[6px] border border-[rgb(34_211_238/0.25)] bg-[rgb(34_211_238/0.1)] text-[#67e8f9]">
              <Database size={11} />
            </span>
            SQL道場
          </span>
          <span className="inline-flex items-center gap-1.5 text-[11px] text-muted-foreground">
            <span className="inline-flex h-[18px] w-[18px] items-center justify-center rounded-[6px] border border-[rgb(168_85_247/0.22)] bg-[rgb(168_85_247/0.1)] text-[#c4b5fd]">
              <MessageSquare size={11} />
            </span>
            フィードバック
          </span>
        </div>
      )}
    </div>
  );
}
