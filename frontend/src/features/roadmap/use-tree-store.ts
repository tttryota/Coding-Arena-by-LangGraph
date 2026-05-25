import { create } from "zustand";

interface TreeState {
  /** The roadmapId this expansion state belongs to */
  initializedFor: string | null;
  expandedIds: Set<string>;
  toggle: (id: string) => void;
  /** Initialize only if not already initialized for this roadmapId */
  initExpanded: (roadmapId: string, majorIds: string[]) => void;
  expandAll: (allIds: string[]) => void;
  collapseAll: () => void;
  isExpanded: (id: string) => boolean;
}

export const useTreeStore = create<TreeState>((set, get) => ({
  initializedFor: null,
  expandedIds: new Set<string>(),

  toggle: (id) =>
    set((state) => {
      const next = new Set(state.expandedIds);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return { expandedIds: next };
    }),

  initExpanded: (roadmapId, majorIds) => {
    if (get().initializedFor === roadmapId) return;
    set({ initializedFor: roadmapId, expandedIds: new Set(majorIds) });
  },

  expandAll: (allIds) =>
    set({ expandedIds: new Set(allIds) }),

  collapseAll: () =>
    set({ expandedIds: new Set<string>() }),

  isExpanded: (id) => get().expandedIds.has(id),
}));
