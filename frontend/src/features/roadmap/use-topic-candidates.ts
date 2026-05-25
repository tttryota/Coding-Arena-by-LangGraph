import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { TopicCandidatesResponse, TopicCandidate } from "@/types/api";

export function useTopicCandidates() {
  return useQuery({
    queryKey: ["topicCandidates"],
    queryFn: async (): Promise<TopicCandidate[]> => {
      const res = await apiFetch("/roadmaps/topics");
      const data = (await res.json()) as TopicCandidatesResponse;
      return data.candidates;
    },
  });
}

export function useRegisterTopic() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async (name: string): Promise<TopicCandidate> => {
      const res = await apiFetch("/roadmaps/topics", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      return res.json() as Promise<TopicCandidate>;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["topicCandidates"] });
    },
  });
}
