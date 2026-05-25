import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { RoadmapTree } from "@/types/api";

export function useRoadmap(roadmapId: string) {
  return useQuery({
    queryKey: ["roadmap", roadmapId],
    queryFn: async () => {
      const res = await apiFetch(`/roadmaps/${roadmapId}`);
      return res.json() as Promise<RoadmapTree>;
    },
  });
}
