import { useMutation, useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type {
  CompetitiveAnswerResponse,
  CompetitiveSessionResponse,
  CompetitiveStartResponse,
  ThemesResponse,
} from "@/types/api";

export function useThemes() {
  return useQuery({
    queryKey: ["competitive-themes"],
    queryFn: async () => {
      const res = await apiFetch("/algorithm-quiz/themes");
      return res.json() as Promise<ThemesResponse>;
    },
  });
}

export function useCompetitiveSession(sessionId: string) {
  return useQuery({
    queryKey: ["competitive-session", sessionId],
    queryFn: async () => {
      const res = await apiFetch(`/algorithm-quiz/sessions/${sessionId}`);
      return res.json() as Promise<CompetitiveSessionResponse>;
    },
    enabled: !!sessionId,
  });
}

export function useStartSession() {
  return useMutation({
    mutationFn: async (themeId?: string) => {
      const body = themeId ? JSON.stringify({ theme_id: themeId }) : undefined;
      const res = await apiFetch("/algorithm-quiz/sessions", {
        method: "POST",
        headers: body ? { "Content-Type": "application/json" } : undefined,
        body,
      });
      return res.json() as Promise<CompetitiveStartResponse>;
    },
  });
}

export function useSubmitAnswer(sessionId: string) {
  return useMutation({
    mutationFn: async (userCode: string) => {
      const res = await apiFetch(
        `/algorithm-quiz/sessions/${sessionId}/answer`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_code: userCode }),
        },
      );
      return res.json() as Promise<CompetitiveAnswerResponse>;
    },
  });
}
