import { create } from "zustand";
import type {
  CompetitiveAnswerResponse,
  CompetitiveChatMessage,
  CompetitiveStartResponse,
} from "@/types/api";

export type CompetitivePhase = "landing" | "problem" | "result";

interface CompetitiveState {
  phase: CompetitivePhase;
  session: CompetitiveStartResponse | null;
  result: CompetitiveAnswerResponse | null;
  chatMessages: CompetitiveChatMessage[];
  codeDraft: string;
  chatDraft: string;
  isSubmitting: boolean;
  isQuestionSubmitting: boolean;
}

interface CompetitiveActions {
  setPhase: (phase: CompetitivePhase) => void;
  setSession: (session: CompetitiveStartResponse) => void;
  setResult: (result: CompetitiveAnswerResponse) => void;
  setCodeDraft: (code: string) => void;
  addChatMessage: (message: CompetitiveChatMessage) => void;
  setChatDraft: (draft: string) => void;
  setIsSubmitting: (v: boolean) => void;
  setIsQuestionSubmitting: (v: boolean) => void;
  reset: () => void;
}

const initialState: CompetitiveState = {
  phase: "landing",
  session: null,
  result: null,
  chatMessages: [],
  codeDraft: "",
  chatDraft: "",
  isSubmitting: false,
  isQuestionSubmitting: false,
};

export const useCompetitiveStore = create<
  CompetitiveState & CompetitiveActions
>((set) => ({
  ...initialState,
  setPhase: (phase) => set({ phase }),
  setSession: (session) =>
    set({
      session,
      phase: "problem",
      chatMessages: [],
      codeDraft: "",
      chatDraft: "",
      result: null,
      isSubmitting: false,
      isQuestionSubmitting: false,
    }),
  setResult: (result) => set({ result, phase: "result" }),
  setCodeDraft: (codeDraft) => set({ codeDraft }),
  addChatMessage: (message) =>
    set((state) => ({ chatMessages: [...state.chatMessages, message] })),
  setChatDraft: (chatDraft) => set({ chatDraft }),
  setIsSubmitting: (isSubmitting) => set({ isSubmitting }),
  setIsQuestionSubmitting: (isQuestionSubmitting) =>
    set({ isQuestionSubmitting }),
  reset: () => set(initialState),
}));
