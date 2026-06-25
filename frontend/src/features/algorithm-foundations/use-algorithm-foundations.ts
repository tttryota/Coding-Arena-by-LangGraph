import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type {
  AlgorithmFoundationAnswerResponse,
  AlgorithmFoundationCatalogResponse,
  AlgorithmFoundationSessionListResponse,
  AlgorithmFoundationSessionResponse,
  AlgorithmFoundationStartResponse,
  AlgorithmFoundationUnitDetailResponse,
  CompetitiveLanguagesResponse,
} from "@/types/api";

export function useAlgorithmFoundationsCatalog() {
  return useQuery({
    queryKey: ["algorithm-foundations-catalog"],
    queryFn: async () => {
      const res = await apiFetch("/algorithm-foundations/catalog");
      return res.json() as Promise<AlgorithmFoundationCatalogResponse>;
    },
  });
}

export function useAlgorithmFoundationLanguages() {
  return useQuery({
    queryKey: ["algorithm-foundations-languages"],
    queryFn: async () => {
      const res = await apiFetch("/algorithm-foundations/languages");
      return res.json() as Promise<CompetitiveLanguagesResponse>;
    },
  });
}

export function useAlgorithmFoundationSessions() {
  return useQuery({
    queryKey: ["algorithm-foundations-sessions"],
    queryFn: async () => {
      const res = await apiFetch("/algorithm-foundations/sessions");
      return res.json() as Promise<AlgorithmFoundationSessionListResponse>;
    },
  });
}

export function useAlgorithmFoundationSession(sessionId: string) {
  return useQuery({
    queryKey: ["algorithm-foundations-session", sessionId],
    queryFn: async () => {
      const res = await apiFetch(`/algorithm-foundations/sessions/${sessionId}`);
      return res.json() as Promise<AlgorithmFoundationSessionResponse>;
    },
    enabled: !!sessionId,
  });
}

export function useAlgorithmFoundationUnit(unitId: string) {
  return useQuery({
    queryKey: ["algorithm-foundations-unit", unitId],
    queryFn: async () => {
      const res = await apiFetch(`/algorithm-foundations/units/${unitId}`);
      return res.json() as Promise<AlgorithmFoundationUnitDetailResponse>;
    },
    enabled: !!unitId,
  });
}

export function useStartAlgorithmFoundationSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload?: {
      unitId?: string;
      problemId?: string;
      programmingLanguage?: string;
    }) => {
      const res = await apiFetch("/algorithm-foundations/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          unit_id: payload?.unitId,
          problem_id: payload?.problemId,
          programming_language: payload?.programmingLanguage,
        }),
      });
      return res.json() as Promise<AlgorithmFoundationStartResponse>;
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: ["algorithm-foundations-catalog"],
        }),
        queryClient.invalidateQueries({
          queryKey: ["algorithm-foundations-sessions"],
        }),
      ]);
    },
  });
}

export function useSubmitAlgorithmFoundationAnswer(sessionId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (userCode: string) => {
      const res = await apiFetch(
        `/algorithm-foundations/sessions/${sessionId}/answer`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_code: userCode }),
        },
      );
      return res.json() as Promise<AlgorithmFoundationAnswerResponse>;
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: ["algorithm-foundations-catalog"],
        }),
        queryClient.invalidateQueries({
          queryKey: ["algorithm-foundations-sessions"],
        }),
        queryClient.invalidateQueries({
          queryKey: ["algorithm-foundations-session", sessionId],
        }),
        queryClient.invalidateQueries({
          queryKey: ["algorithm-foundations-unit"],
        }),
      ]);
    },
  });
}
