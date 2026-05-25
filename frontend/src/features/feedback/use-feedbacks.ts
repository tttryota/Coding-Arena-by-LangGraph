import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { FeedbackListResponse } from "@/types/api";

export interface FeedbackFilters {
  dateFrom: string | null;
  dateTo: string | null;
  readStatus: "all" | "unread" | "read";
}

/**
 * Convert a date input value (YYYY-MM-DD) to an ISO 8601 string with
 * the browser's timezone offset at the actual time point.
 * - "from" (end=false): start of the day  (e.g. 2026-05-20T00:00:00+09:00)
 * - "to"   (end=true):  end of the day    (e.g. 2026-05-20T23:59:59.999+09:00)
 *   The backend uses `created_at <= date_to` (inclusive), so T23:59:59.999
 *   covers effectively all instants within the day.
 */
export function toIso(date: string, end: boolean): string {
  // Construct the Date at the target time to get the correct TZ offset
  // (matters if the timezone observes DST)
  const d = end
    ? new Date(`${date}T23:59:59`)
    : new Date(`${date}T00:00:00`);
  const pad = (n: number) => String(n).padStart(2, "0");
  const offset = -d.getTimezoneOffset();
  const sign = offset >= 0 ? "+" : "-";
  const absOffset = Math.abs(offset);
  const oh = pad(Math.floor(absOffset / 60));
  const om = pad(absOffset % 60);
  const tz = `${sign}${oh}:${om}`;

  if (end) {
    return `${date}T23:59:59.999${tz}`;
  }
  return `${date}T00:00:00${tz}`;
}

export function useFeedbacks(filters: FeedbackFilters) {
  return useQuery({
    queryKey: ["feedbacks", filters],
    placeholderData: keepPreviousData,
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters.dateFrom)
        params.set("date_from", toIso(filters.dateFrom, false));
      if (filters.dateTo) params.set("date_to", toIso(filters.dateTo, true));
      if (filters.readStatus !== "all")
        params.set("read_status", filters.readStatus);
      const qs = params.toString();
      const url = `/ingestion/feedbacks${qs ? `?${qs}` : ""}`;
      const res = await apiFetch(url);
      return res.json() as Promise<FeedbackListResponse>;
    },
  });
}
