import { useMutation } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { PracticeStartResponse } from "@/types/api";

export function useStartPractice(sessionId: string) {
  return useMutation({
    mutationFn: async () => {
      const res = await apiFetch(`/sessions/${sessionId}/practice/start`, {
        method: "POST",
      });
      return res.json() as Promise<PracticeStartResponse>;
    },
  });
}
