import { useMutation } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { StartSessionResponse } from "@/types/api";

export function useStartSession() {
  return useMutation({
    mutationFn: async (roadmapItemId: string) => {
      const res = await apiFetch("/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ roadmap_item_id: roadmapItemId }),
      });
      return res.json() as Promise<StartSessionResponse>;
    },
  });
}
