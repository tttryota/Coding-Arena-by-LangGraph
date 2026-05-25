import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { SessionDetailResponse } from "@/types/api";

export function useSession(sessionId: string) {
  return useQuery({
    queryKey: ["session", sessionId],
    queryFn: async () => {
      const res = await apiFetch(`/sessions/${sessionId}`);
      return res.json() as Promise<SessionDetailResponse>;
    },
  });
}
