import { useMutation } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { SessionState, CodingSessionStateDTO } from "@/types/api";

export function useSubmitInput(sessionId: string) {
  return useMutation({
    mutationFn: async (body: {
      user_input: string;
      input_source: "form" | "chat";
    }) => {
      const res = await apiFetch(`/sessions/${sessionId}/input`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      return res.json() as Promise<SessionState | CodingSessionStateDTO>;
    },
  });
}
