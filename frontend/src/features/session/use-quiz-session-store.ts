import { create } from "zustand";
import type { SessionState } from "@/types/api";

export type QuizPhase =
  | "learning"
  | "question"
  | "feedback"
  | "explanation"
  | "chat_response"
  | "summary";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

interface QuizSessionState {
  phase: QuizPhase;
  sessionState: SessionState | null;
  chatMessages: ChatMessage[];
  answerDraft: string;
  chatDraft: string;
  isSubmitting: boolean;
  /** 解説表示用テキスト（backend の explanation_text に対応） */
  explanationText: string;
  /** 直近のチャット応答テキスト（backend の chat_response_text に対応） */
  lastChatResponse: string;
  /** フェーズ遷移前の問題テキストのスナップショット（解説画面で使用） */
  questionSnapshot: { text: string; number: number } | null;

  setPhase: (phase: QuizPhase) => void;
  setSessionState: (state: SessionState) => void;
  addChatMessage: (msg: ChatMessage) => void;
  setAnswerDraft: (text: string) => void;
  setChatDraft: (text: string) => void;
  setIsSubmitting: (flag: boolean) => void;
  setExplanationText: (text: string) => void;
  setLastChatResponse: (text: string) => void;
  setQuestionSnapshot: (snapshot: { text: string; number: number } | null) => void;
  reset: () => void;
}

const initialState = {
  phase: "question" as QuizPhase,
  sessionState: null as SessionState | null,
  chatMessages: [] as ChatMessage[],
  answerDraft: "",
  chatDraft: "",
  isSubmitting: false,
  explanationText: "",
  lastChatResponse: "",
  questionSnapshot: null as { text: string; number: number } | null,
};

export const useQuizSessionStore = create<QuizSessionState>((set) => ({
  ...initialState,

  setPhase: (phase) => set({ phase }),

  setSessionState: (sessionState) => set({ sessionState }),

  addChatMessage: (msg) =>
    set((state) => ({ chatMessages: [...state.chatMessages, msg] })),

  setAnswerDraft: (answerDraft) => set({ answerDraft }),

  setChatDraft: (chatDraft) => set({ chatDraft }),

  setIsSubmitting: (isSubmitting) => set({ isSubmitting }),

  setExplanationText: (explanationText) => set({ explanationText }),

  setLastChatResponse: (lastChatResponse) => set({ lastChatResponse }),

  setQuestionSnapshot: (questionSnapshot) => set({ questionSnapshot }),

  reset: () => set(initialState),
}));
