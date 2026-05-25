import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { FeedbackListItem, FeedbackListResponse } from "@/types/api";
function isListQuery(queryKey: readonly unknown[]): boolean {
  return (
    queryKey[0] === "feedbacks" &&
    queryKey.length === 2 &&
    typeof queryKey[1] === "object" &&
    queryKey[1] !== null
  );
}

/**
 * Extract the read status filter from a list query key.
 * Handles both our FeedbackFilters shape ({ readStatus }) and potential
 * alternative shapes ({ read_status }) for defensive compatibility.
 */
function getReadStatus(queryKey: readonly unknown[]): string | undefined {
  const obj = queryKey[1] as Record<string, unknown> | undefined;
  if (!obj) return undefined;
  if (typeof obj.readStatus === "string") return obj.readStatus;
  if (typeof obj.read_status === "string") return obj.read_status;
  return undefined;
}

export function useMarkAsRead() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async (feedbackId: string) => {
      const res = await apiFetch(`/ingestion/feedbacks/${feedbackId}/read`, {
        method: "PUT",
      });
      return res.json() as Promise<FeedbackListItem>;
    },
    onMutate: async (feedbackId) => {
      // Cancel outgoing refetches for list queries only
      await qc.cancelQueries({
        predicate: (query) => isListQuery(query.queryKey),
      });
      await qc.cancelQueries({ queryKey: ["feedbacks", "unreadCount"] });

      // Snapshot previous list data for rollback
      const previousQueries = qc.getQueriesData<FeedbackListResponse>({
        predicate: (query) => isListQuery(query.queryKey),
      });

      // Snapshot previous unread count for rollback
      const previousUnreadCount = qc.getQueryData<number>([
        "feedbacks",
        "unreadCount",
      ]);

      // Check if the item was actually unread (for idempotent count updates)
      let wasUnread = false;
      for (const [, data] of previousQueries) {
        if (!data) continue;
        const item = data.items.find((i) => i.id === feedbackId);
        if (item) {
          wasUnread = !item.is_read;
          break;
        }
      }

      // Optimistically update each list query individually
      // (setQueriesData updater only takes 1 arg, so we iterate manually
      // to read the queryKey for filter-aware updates)
      for (const [queryKey, data] of previousQueries) {
        if (!data) continue;
        const readStatus = getReadStatus(queryKey);

        const now = new Date().toISOString();

        if (readStatus === "unread") {
          // Remove the item from unread-filtered list
          const filtered = data.items.filter((item) => item.id !== feedbackId);
          qc.setQueryData<FeedbackListResponse>(queryKey, {
            ...data,
            items: filtered,
            total_count: filtered.length,
          });
        } else if (readStatus === "read") {
          // For "read" filter: mark as read, and if the item wasn't already
          // in this cache (e.g. just became read), add it
          const exists = data.items.some((item) => item.id === feedbackId);
          if (exists) {
            qc.setQueryData<FeedbackListResponse>(queryKey, {
              ...data,
              items: data.items.map((item) =>
                item.id === feedbackId && !item.is_read
                  ? { ...item, is_read: true, read_at: now }
                  : item,
              ),
            });
          }
          // If not in "read" cache, onSettled invalidation will add it
        } else {
          // For "all" or unrecognized filters, just mark as read in place
          qc.setQueryData<FeedbackListResponse>(queryKey, {
            ...data,
            items: data.items.map((item) =>
              item.id === feedbackId && !item.is_read
                ? { ...item, is_read: true, read_at: now }
                : item,
            ),
          });
        }
      }

      // Only decrement unread count if the item was actually unread
      if (
        wasUnread &&
        previousUnreadCount != null &&
        previousUnreadCount > 0
      ) {
        qc.setQueryData<number>(
          ["feedbacks", "unreadCount"],
          previousUnreadCount - 1,
        );
      }

      return { previousQueries, previousUnreadCount };
    },
    onError: (_err, _feedbackId, context) => {
      if (context?.previousQueries) {
        for (const [key, data] of context.previousQueries) {
          qc.setQueryData(key, data);
        }
      }
      if (context?.previousUnreadCount != null) {
        qc.setQueryData<number>(
          ["feedbacks", "unreadCount"],
          context.previousUnreadCount,
        );
      }
    },
    onSettled: () => {
      void qc.invalidateQueries({ queryKey: ["feedbacks"] });
    },
  });
}
