import { create } from "zustand";
import type {
  CompetitiveChatMessage,
  SqlDojoAnswerResponse,
  SqlDojoStartResponse,
} from "@/types/api";

export type SqlDojoPhase = "landing" | "problem" | "result";

interface SqlDojoState {
  phase: SqlDojoPhase;
  session: SqlDojoStartResponse | null;
  result: SqlDojoAnswerResponse | null;
  chatMessages: CompetitiveChatMessage[];
  sqlDraft: string;
  chatDraft: string;
  isSubmitting: boolean;
  isQuestionSubmitting: boolean;
}

interface SqlDojoActions {
  setSession: (session: SqlDojoStartResponse) => void;
  setResult: (result: SqlDojoAnswerResponse) => void;
  setSqlDraft: (sql: string) => void;
  addChatMessage: (message: CompetitiveChatMessage) => void;
  setChatDraft: (draft: string) => void;
  setIsSubmitting: (v: boolean) => void;
  setIsQuestionSubmitting: (v: boolean) => void;
  reset: () => void;
}

const initialState: SqlDojoState = {
  phase: "landing",
  session: null,
  result: null,
  chatMessages: [],
  sqlDraft: "",
  chatDraft: "",
  isSubmitting: false,
  isQuestionSubmitting: false,
};

export const useSqlDojoStore = create<SqlDojoState & SqlDojoActions>((set) => ({
  ...initialState,
  setSession: (session) =>
    set({
      session,
      phase: "problem",
      result: null,
      chatMessages: [],
      sqlDraft: "",
      chatDraft: "",
      isSubmitting: false,
      isQuestionSubmitting: false,
    }),
  setResult: (result) => set({ result, phase: "result" }),
  setSqlDraft: (sqlDraft) => set({ sqlDraft }),
  addChatMessage: (message) =>
    set((state) => ({ chatMessages: [...state.chatMessages, message] })),
  setChatDraft: (chatDraft) => set({ chatDraft }),
  setIsSubmitting: (isSubmitting) => set({ isSubmitting }),
  setIsQuestionSubmitting: (isQuestionSubmitting) =>
    set({ isQuestionSubmitting }),
  reset: () => set(initialState),
}));
