import { useState, useEffect, useCallback, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { Bell, CheckCheck, AlertTriangle, X } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { useFeedbacks } from "./use-feedbacks";
import { useMarkAsRead } from "./use-mark-as-read";
import { useFeedbackFilters } from "./use-feedback-filters";
import { FeedbackFilters } from "./feedback-filters";
import { FeedbackCard } from "./feedback-card";
import { FeedbackSkeletonCard } from "./feedback-skeleton";
import { EmptyNoData, EmptyFiltered } from "./feedback-empty";

export function FeedbackListPage() {
  const navigate = useNavigate();

  // Filter state from Zustand
  const dateFrom = useFeedbackFilters((s) => s.dateFrom);
  const dateTo = useFeedbackFilters((s) => s.dateTo);
  const readStatus = useFeedbackFilters((s) => s.readStatus);
  const setDateFrom = useFeedbackFilters((s) => s.setDateFrom);
  const setDateTo = useFeedbackFilters((s) => s.setDateTo);
  const setReadStatus = useFeedbackFilters((s) => s.setReadStatus);
  const resetFilters = useFeedbackFilters((s) => s.reset);

  // Debounced date values (300ms debounce for date inputs, immediate for select)
  const [debouncedDateFrom, setDebouncedDateFrom] = useState(dateFrom);
  const [debouncedDateTo, setDebouncedDateTo] = useState(dateTo);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedDateFrom(dateFrom), 300);
    return () => clearTimeout(timer);
  }, [dateFrom]);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedDateTo(dateTo), 300);
    return () => clearTimeout(timer);
  }, [dateTo]);

  const filters = {
    dateFrom: debouncedDateFrom,
    dateTo: debouncedDateTo,
    readStatus,
  };
  const isDirty =
    dateFrom !== null || dateTo !== null || readStatus !== "all";

  const { data, isLoading, isError, errorUpdatedAt, refetch } = useFeedbacks(filters);
  const markAsRead = useMarkAsRead();

  const [dismissedErrorAt, setDismissedErrorAt] = useState<number | null>(null);
  const showErrorToast =
    isError && errorUpdatedAt > 0 && dismissedErrorAt !== errorUpdatedAt;

  // Expanded card IDs
  const [expanded, setExpanded] = useState<Set<string>>(() => new Set());
  const toggleExpand = useCallback((id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const items = useMemo(() => data?.items ?? [], [data]);
  const totalCount = data?.total_count ?? 0;
  const unreadCount = items.filter((f) => !f.is_read).length;

  const handleMarkRead = useCallback(
    (feedbackId: string) => {
      markAsRead.mutate(feedbackId);
    },
    [markAsRead],
  );

  const handleMarkAllRead = useCallback(() => {
    for (const item of items) {
      if (!item.is_read) {
        markAsRead.mutate(item.id);
      }
    }
  }, [items, markAsRead]);

  const handleOpenRoadmap = useCallback(() => {
    // TODO: resolve roadmap_item_id → roadmap_id when backend supports it
    // For now, navigate to roadmap list as the ID resolution API is not available
    navigate("/roadmaps");
  }, [navigate]);

  const crumbs = [{ label: "フィードバック" }];

  // Show header action when data is available (even during background refetch errors)
  const hasData = items.length > 0;
  const headerAction =
    hasData && unreadCount > 0 ? (
      <Button variant="outline" size="sm" onClick={handleMarkAllRead}>
        <CheckCheck className="h-3.5 w-3.5" />
        すべて既読にする
      </Button>
    ) : undefined;

  // State conditions:
  // - Loading: only on initial load (no data yet)
  // - Error toast: shown via toast, preserving existing data
  // - Empty states: only when not loading and no error (or data exists)
  const isInitialLoad = isLoading && !data;
  const showEmptyNoData = !isLoading && !isError && items.length === 0 && !isDirty;
  const showEmptyFiltered = !isLoading && !isError && items.length === 0 && isDirty;

  return (
    <>
      <AppShell crumbs={crumbs} action={headerAction}>
        {/* Page header */}
        <div className="mb-6">
          <h1 className="text-xl font-semibold tracking-tight">
            フィードバック
          </h1>
          <div className="mt-1.5 inline-flex flex-wrap items-baseline gap-1 text-[13px] text-muted-foreground">
            {isInitialLoad && <span>読み込み中…</span>}
            {!isInitialLoad && !data && isError && <span>—</span>}
            {showEmptyNoData && <span>0件</span>}
            {(hasData || showEmptyFiltered) && (
              <>
                <b className="font-mono text-sm font-semibold tabular-nums text-foreground">
                  {totalCount}
                </b>
                <span>件</span>
                {unreadCount > 0 && (
                  <span className="ml-2 inline-flex items-center gap-1 rounded-full border border-[rgb(37_99_235/0.25)] bg-[rgb(37_99_235/0.12)] px-2 py-px text-[11px] font-medium text-primary">
                    <Bell className="h-[10px] w-[10px]" />
                    未読 {unreadCount}
                  </span>
                )}
              </>
            )}
          </div>
        </div>

        {/* Filter bar — visible when loaded or loading */}
        {(hasData || isInitialLoad || showEmptyFiltered) && (
          <FeedbackFilters
            dateFrom={dateFrom}
            dateTo={dateTo}
            readStatus={readStatus}
            onDateFromChange={setDateFrom}
            onDateToChange={setDateTo}
            onReadStatusChange={setReadStatus}
            onReset={resetFilters}
            isDirty={isDirty}
          />
        )}

        {/* Loading skeleton */}
        {isInitialLoad && (
          <div className="flex flex-col gap-2.5">
            {[0, 1, 2].map((i) => (
              <FeedbackSkeletonCard key={i} />
            ))}
          </div>
        )}

        {/* List — shown even during background refetch errors */}
        {hasData && (
          <div className="flex flex-col gap-2.5">
            {items.map((item) => (
              <FeedbackCard
                key={item.id}
                item={item}
                expanded={expanded.has(item.id)}
                onToggle={() => toggleExpand(item.id)}
                onMarkRead={() => handleMarkRead(item.id)}
                onOpenRoadmap={() => {
                  if (item.roadmap_item_id) handleOpenRoadmap();
                }}
              />
            ))}
          </div>
        )}

        {/* Empty states */}
        {showEmptyNoData && <EmptyNoData />}
        {showEmptyFiltered && <EmptyFiltered onReset={resetFilters} />}
      </AppShell>

      {/* Error toast — spec: "エラー = Toast通知" */}
      {showErrorToast && (
        <div
          role="alert"
          className="fixed bottom-6 left-1/2 z-40 flex min-w-[320px] -translate-x-1/2 animate-[toast-in_200ms_ease-out] items-center gap-3 rounded-lg border border-[rgb(244_63_94/0.4)] border-l-[3px] border-l-[#fb7185] bg-card px-4 py-3 text-[13px] text-foreground shadow-[0_12px_32px_-8px_rgb(0_0_0/0.6)]"
        >
          <AlertTriangle className="h-4 w-4 shrink-0 text-[#fb7185]" />
          <div className="flex-1">
            <div className="font-medium">
              フィードバック一覧の取得に失敗しました
            </div>
            <div className="mt-0.5 text-xs text-muted-foreground">
              ネットワーク接続を確認するか、少し待ってからもう一度お試しください
            </div>
          </div>
          <button
            type="button"
            className="inline-flex cursor-pointer items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
            onClick={() => {
              setDismissedErrorAt(errorUpdatedAt);
              void refetch();
            }}
          >
            再読み込み
          </button>
          <button
            type="button"
            className="inline-flex cursor-pointer items-center p-1 text-muted-foreground hover:text-foreground"
            onClick={() => setDismissedErrorAt(errorUpdatedAt)}
            aria-label="閉じる"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      )}
    </>
  );
}
