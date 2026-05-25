import { create } from "zustand";

type ReadStatus = "all" | "unread" | "read";

interface FeedbackFilterState {
  dateFrom: string | null;
  dateTo: string | null;
  readStatus: ReadStatus;
  setDateFrom: (v: string | null) => void;
  setDateTo: (v: string | null) => void;
  setReadStatus: (v: ReadStatus) => void;
  reset: () => void;
}

export const useFeedbackFilters = create<FeedbackFilterState>((set) => ({
  dateFrom: null,
  dateTo: null,
  readStatus: "all",
  setDateFrom: (v) => set({ dateFrom: v }),
  setDateTo: (v) => set({ dateTo: v }),
  setReadStatus: (v) => set({ readStatus: v }),
  reset: () => set({ dateFrom: null, dateTo: null, readStatus: "all" }),
}));
