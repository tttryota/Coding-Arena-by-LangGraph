import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { FeedbackListResponse } from "@/types/api";

// フィードバック未読件数を取得する共有フック
// queryKey: ["feedbacks", "unreadCount"]
// フィードバック既読化時に invalidateQueries(["feedbacks", "unreadCount"]) で連動する
export function useUnreadCount(): number {
  const { data } = useQuery({
    queryKey: ["feedbacks", "unreadCount"],
    queryFn: async () => {
      const res = await apiFetch("/ingestion/feedbacks?read_status=unread");
      const json = (await res.json()) as FeedbackListResponse;
      return json.total_count;
    },
    staleTime: 60_000,
  });
  return data ?? 0;
}
