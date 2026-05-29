import { create } from "zustand";
import type { SessionState, CodingSessionStateDTO, CodingDifficultyType } from "@/types/api";

export interface CodingFeedbackSnapshot {
  questionText: string;
  questionNumber: number;
  format?: CodingDifficultyType;
  cpIndex?: number;
}

export type QuizPhase =
  | "lecture"
  | "learning"
  | "question"
  | "feedback"
  | "explanation"
  | "chat_response"
  | "summary";

export type SessionType = "quiz" | "coding";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

interface QuizSessionState {
  phase: QuizPhase;
  sessionType: SessionType;
  sessionState: SessionState | null;
  codingState: CodingSessionStateDTO | null;
  chatMessages: ChatMessage[];
  lectureChatMessages: ChatMessage[];
  answerDraft: string;
  chatDraft: string;
  isSubmitting: boolean;
  /** 解説表示用テキスト（backend の explanation_text に対応） */
  explanationText: string;
  /** 直近のチャット応答テキスト（backend の chat_response_text に対応） */
  lastChatResponse: string;
  /** フェーズ遷移前の問題テキストのスナップショット（解説画面で使用） */
  questionSnapshot: { text: string; number: number; cpIndex?: number } | null;
  /** コーディングセッション: 採点した問題のスナップショット（フィードバック画面で使用） */
  codingFeedbackSnapshot: CodingFeedbackSnapshot | null;

  setPhase: (phase: QuizPhase) => void;
  setSessionType: (type: SessionType) => void;
  setSessionState: (state: SessionState) => void;
  setCodingState: (state: CodingSessionStateDTO) => void;
  addChatMessage: (msg: ChatMessage) => void;
  addLectureChatMessage: (msg: ChatMessage) => void;
  setAnswerDraft: (text: string) => void;
  setChatDraft: (text: string) => void;
  setIsSubmitting: (flag: boolean) => void;
  setExplanationText: (text: string) => void;
  setLastChatResponse: (text: string) => void;
  setQuestionSnapshot: (snapshot: { text: string; number: number; cpIndex?: number } | null) => void;
  setCodingFeedbackSnapshot: (snapshot: CodingFeedbackSnapshot | null) => void;
  reset: () => void;
}

const initialState = {
  phase: "question" as QuizPhase,
  sessionType: "quiz" as SessionType,
  sessionState: null as SessionState | null,
  codingState: null as CodingSessionStateDTO | null,
  chatMessages: [] as ChatMessage[],
  lectureChatMessages: [] as ChatMessage[],
  answerDraft: "",
  chatDraft: "",
  isSubmitting: false,
  explanationText: "",
  lastChatResponse: "",
  questionSnapshot: null as { text: string; number: number } | null,
  codingFeedbackSnapshot: null as CodingFeedbackSnapshot | null,
};

export const useQuizSessionStore = create<QuizSessionState>((set) => ({
  ...initialState,

  setPhase: (phase) => set({ phase }),

  setSessionType: (sessionType) => set({ sessionType }),

  setSessionState: (sessionState) => set({ sessionState }),

  setCodingState: (codingState) => set({ codingState }),

  addChatMessage: (msg) =>
    set((state) => ({ chatMessages: [...state.chatMessages, msg] })),

  addLectureChatMessage: (msg) =>
    set((state) => ({
      lectureChatMessages: [...state.lectureChatMessages, msg],
    })),

  setAnswerDraft: (answerDraft) => set({ answerDraft }),

  setChatDraft: (chatDraft) => set({ chatDraft }),

  setIsSubmitting: (isSubmitting) => set({ isSubmitting }),

  setExplanationText: (explanationText) => set({ explanationText }),

  setLastChatResponse: (lastChatResponse) => set({ lastChatResponse }),

  setQuestionSnapshot: (questionSnapshot) => set({ questionSnapshot }),

  setCodingFeedbackSnapshot: (codingFeedbackSnapshot) =>
    set({ codingFeedbackSnapshot }),

  reset: () => set(initialState),
}));
