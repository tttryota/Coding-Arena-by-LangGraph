import { useMutation, useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type {
  CompetitiveChatMessage,
  SqlDojoAnswerResponse,
  SqlDojoCatalogResponse,
  SqlDojoDifficulty,
  SqlDojoQuestionResponse,
  SqlDojoSessionListResponse,
  SqlDojoSessionResponse,
  SqlDojoStartResponse,
} from "@/types/api";

export function useSqlDojoCatalog() {
  return useQuery({
    queryKey: ["sql-dojo-catalog"],
    queryFn: async () => {
      const res = await apiFetch("/sql-dojo/catalog");
      return res.json() as Promise<SqlDojoCatalogResponse>;
    },
  });
}

export function useSqlDojoSessions() {
  return useQuery({
    queryKey: ["sql-dojo-sessions"],
    queryFn: async () => {
      const res = await apiFetch("/sql-dojo/sessions");
      return res.json() as Promise<SqlDojoSessionListResponse>;
    },
  });
}

export function useSqlDojoSession(sessionId: string) {
  return useQuery({
    queryKey: ["sql-dojo-session", sessionId],
    queryFn: async () => {
      const res = await apiFetch(`/sql-dojo/sessions/${sessionId}`);
      return res.json() as Promise<SqlDojoSessionResponse>;
    },
    enabled: !!sessionId,
  });
}

export function useStartSqlDojoSession() {
  return useMutation({
    mutationFn: async (body: {
      difficulty: SqlDojoDifficulty;
      themeFamily?: string;
      topicId?: string;
    }) => {
      const res = await apiFetch("/sql-dojo/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          difficulty: body.difficulty,
          theme_family: body.themeFamily,
          topic_id: body.topicId,
        }),
      });
      return res.json() as Promise<SqlDojoStartResponse>;
    },
  });
}

export function useSubmitSqlDojoAnswer(sessionId: string) {
  return useMutation({
    mutationFn: async (userSql: string) => {
      const res = await apiFetch(`/sql-dojo/sessions/${sessionId}/answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_sql: userSql }),
      });
      return res.json() as Promise<SqlDojoAnswerResponse>;
    },
  });
}

export function useAskSqlDojoQuestion(sessionId: string) {
  return useMutation({
    mutationFn: async (body: {
      user_input: string;
      history: CompetitiveChatMessage[];
    }) => {
      const res = await apiFetch(`/sql-dojo/sessions/${sessionId}/question`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      return res.json() as Promise<SqlDojoQuestionResponse>;
    },
  });
}
