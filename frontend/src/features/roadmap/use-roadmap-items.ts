import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type {
  AddItemResponse,
  MoveItemResponse,
  DeleteItemResponse,
} from "@/types/api";

export function useAddItem(roadmapId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      parent_id: string | null;
      title: string;
      description: string;
    }) => {
      const res = await apiFetch(`/roadmaps/${roadmapId}/items`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      return res.json() as Promise<AddItemResponse>;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["roadmap", roadmapId] });
    },
  });
}

export function useMoveItem(roadmapId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      itemId,
      targetParentId,
      targetOrder,
    }: {
      itemId: string;
      targetParentId: string | null;
      targetOrder: number;
    }) => {
      const res = await apiFetch(
        `/roadmaps/${roadmapId}/items/${itemId}/move`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            target_parent_id: targetParentId,
            target_order: targetOrder,
          }),
        },
      );
      return res.json() as Promise<MoveItemResponse>;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["roadmap", roadmapId] });
    },
  });
}

export function useDeleteItem(roadmapId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (itemId: string) => {
      const res = await apiFetch(
        `/roadmaps/${roadmapId}/items/${itemId}`,
        { method: "DELETE" },
      );
      return res.json() as Promise<DeleteItemResponse>;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["roadmap", roadmapId] });
    },
  });
}
