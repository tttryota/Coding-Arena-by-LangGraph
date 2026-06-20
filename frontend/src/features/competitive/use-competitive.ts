import { useMutation, useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type {
  CompetitiveAnswerResponse,
  CompetitiveChatMessage,
  CompetitiveLanguagesResponse,
  CompetitiveQuestionResponse,
  CompetitiveSessionListResponse,
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

export function useCompetitiveLanguages() {
  return useQuery({
    queryKey: ["competitive-languages"],
    queryFn: async () => {
      const res = await apiFetch("/algorithm-quiz/languages");
      return res.json() as Promise<CompetitiveLanguagesResponse>;
    },
  });
}

export function useCompetitiveSessions() {
  return useQuery({
    queryKey: ["competitive-sessions"],
    queryFn: async () => {
      const res = await apiFetch("/algorithm-quiz/sessions");
      return res.json() as Promise<CompetitiveSessionListResponse>;
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
    mutationFn: async (params: {
      themeId?: string;
      programmingLanguage: string;
    }) => {
      const body = JSON.stringify({
        theme_id: params.themeId,
        programming_language: params.programmingLanguage,
      });
      const res = await apiFetch("/algorithm-quiz/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
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

export function useAskQuestion(sessionId: string) {
  return useMutation({
    mutationFn: async (body: {
      user_input: string;
      history: CompetitiveChatMessage[];
    }) => {
      const res = await apiFetch(
        `/algorithm-quiz/sessions/${sessionId}/question`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        },
      );
      return res.json() as Promise<CompetitiveQuestionResponse>;
    },
  });
}
