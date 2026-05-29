import { create } from "zustand";
import type {
  CompetitiveAnswerResponse,
  CompetitiveStartResponse,
} from "@/types/api";

export type CompetitivePhase = "landing" | "problem" | "result";

interface CompetitiveState {
  phase: CompetitivePhase;
  session: CompetitiveStartResponse | null;
  result: CompetitiveAnswerResponse | null;
  codeDraft: string;
  isSubmitting: boolean;
}

interface CompetitiveActions {
  setPhase: (phase: CompetitivePhase) => void;
  setSession: (session: CompetitiveStartResponse) => void;
  setResult: (result: CompetitiveAnswerResponse) => void;
  setCodeDraft: (code: string) => void;
  setIsSubmitting: (v: boolean) => void;
  reset: () => void;
}

const initialState: CompetitiveState = {
  phase: "landing",
  session: null,
  result: null,
  codeDraft: "",
  isSubmitting: false,
};

export const useCompetitiveStore = create<
  CompetitiveState & CompetitiveActions
>((set) => ({
  ...initialState,
  setPhase: (phase) => set({ phase }),
  setSession: (session) => set({ session, phase: "problem" }),
  setResult: (result) => set({ result, phase: "result" }),
  setCodeDraft: (codeDraft) => set({ codeDraft }),
  setIsSubmitting: (isSubmitting) => set({ isSubmitting }),
  reset: () => set(initialState),
}));
