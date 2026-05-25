import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { RoadmapListResponse } from "@/types/api";

export function useRoadmaps() {
  return useQuery({
    queryKey: ["roadmaps"],
    queryFn: async (): Promise<RoadmapListResponse> => {
      const res = await apiFetch("/roadmaps");
      return res.json() as Promise<RoadmapListResponse>;
    },
  });
}
