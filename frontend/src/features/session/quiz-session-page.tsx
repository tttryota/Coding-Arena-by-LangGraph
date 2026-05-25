import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import {
  AlertTriangle,
  ArrowLeft,
  Clock,
  Pause,
  RotateCcw,
  SearchX,
} from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api";
import { useSession } from "./use-session";
import { useSubmitInput } from "./use-submit-input";
import { useQuizSessionStore } from "./use-quiz-session-store";
import { SessionHeader } from "./session-header";
import { QuestionPhase } from "./question-phase";
import { FeedbackPhase } from "./feedback-phase";
import { ExplanationPhase } from "./explanation-phase";
import { SummaryPhase } from "./summary-phase";
import { SessionProgress } from "./session-progress";
import { MainSkeleton, SidebarSkeleton } from "./session-skeleton";
import { ErrorToast } from "./error-toast";

/** Navigation state passed from roadmap detail page */
interface LocationState {
  topic?: string;
  roadmapId?: string;
}

export function QuizSessionPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const locState = (location.state ?? {}) as LocationState;

  const { data, isLoading, isError, error } = useSession(sessionId ?? "");
  const submitInput = useSubmitInput(sessionId ?? "");

  const {
    phase,
    sessionState,
    chatMessages,
    answerDraft,
    chatDraft,
    isSubmitting,
    explanationText,
    questionSnapshot,
    setPhase,
    setSessionState,
    addChatMessage,
    setAnswerDraft,
    setChatDraft,
    setIsSubmitting,
    setExplanationText,
    setLastChatResponse,
    setQuestionSnapshot,
    reset,
  } = useQuizSessionStore();

  const [showToast, setShowToast] = useState(false);

  // Reset store on unmount or sessionId change
  useEffect(() => {
    return () => {
      reset();
    };
  }, [sessionId, reset]);

  // Initialize sessionState from API response.
  // When backend returns full SessionState from GET /sessions/:id,
  // all fields will be populated. Currently only metadata is returned,
  // so we build a minimal state. The response is spread to pick up
  // any additional fields the backend may return in the future.
  useEffect(() => {
    if (data && !sessionState) {
      setSessionState({
        session_id: data.session_id,
        roadmap_item_id: data.session.roadmap_item_id,
        roadmap_item_level: "detail",
        roadmap_item_title: locState.topic ?? "",
        roadmap_item_description: "",
        is_resumed: false,
        // Spread any extra SessionState fields the backend may include
        ...("confirmation_points" in data ? data : {}),
      } as import("@/types/api").SessionState);

      // If session is completed, go to summary phase
      if (data.session.status === "completed") {
        setPhase("summary");
      }
    }
  }, [data, sessionState, setSessionState, setPhase, locState.topic]);

  const handleSubmitAnswer = useCallback(
    async (text: string) => {
      if (!sessionId || isSubmitting) return;
      // Snapshot current question before submitting
      if (sessionState?.current_question_text) {
        setQuestionSnapshot({
          text: sessionState.current_question_text,
          number: sessionState.total_questions_asked ?? 1,
        });
      }
      setIsSubmitting(true);
      try {
        const result = await submitInput.mutateAsync({
          user_input: text,
          input_source: "form",
        });
        setSessionState(result);
        setAnswerDraft("");
        // input_type determines phase transition
        if (result.input_type === "answer") {
          setPhase("feedback");
        }
      } catch (err) {
        if (err instanceof ApiError && err.status === 503) {
          setShowToast(true);
        }
      } finally {
        setIsSubmitting(false);
      }
    },
    [
      sessionId,
      isSubmitting,
      sessionState,
      submitInput,
      setSessionState,
      setAnswerDraft,
      setPhase,
      setIsSubmitting,
      setQuestionSnapshot,
      setShowToast,
    ],
  );

  const handleSubmitChat = useCallback(
    async (text: string) => {
      if (!sessionId || isSubmitting) return;
      // Snapshot for explanation
      if (sessionState?.current_question_text) {
        setQuestionSnapshot({
          text: sessionState.current_question_text,
          number: sessionState.total_questions_asked ?? 1,
        });
      }
      setIsSubmitting(true);
      addChatMessage({ role: "user", content: text });
      setChatDraft("");
      try {
        const result = await submitInput.mutateAsync({
          user_input: text,
          input_source: "chat",
        });
        setSessionState(result);
        if (result.input_type === "answer") {
          setPhase("feedback");
        } else if (result.input_type === "explanation_request") {
          setExplanationText(result.explanation_text ?? "");
          setPhase("explanation");
        } else if (result.input_type === "question") {
          setLastChatResponse(result.chat_response_text ?? "");
          addChatMessage({
            role: "assistant",
            content: result.chat_response_text ?? "",
          });
          setPhase("question");
        }
      } catch (err) {
        if (err instanceof ApiError && err.status === 503) {
          setShowToast(true);
        }
      } finally {
        setIsSubmitting(false);
      }
    },
    [
      sessionId,
      isSubmitting,
      sessionState,
      submitInput,
      setSessionState,
      setChatDraft,
      setPhase,
      setIsSubmitting,
      setExplanationText,
      setLastChatResponse,
      addChatMessage,
      setQuestionSnapshot,
      setShowToast,
    ],
  );

  const handleExplain = useCallback(() => {
    void handleSubmitChat("解説してください");
  }, [handleSubmitChat]);

  const handleNext = useCallback(() => {
    if (sessionState?.next_action === "complete") {
      setPhase("summary");
    } else {
      setPhase("question");
      setAnswerDraft("");
    }
  }, [sessionState, setPhase, setAnswerDraft]);

  const handleContinue = useCallback(() => {
    setPhase("question");
    setAnswerDraft("");
  }, [setPhase, setAnswerDraft]);

  const handleBack = useCallback(() => {
    if (locState.roadmapId) {
      navigate(`/roadmaps/${locState.roadmapId}`);
    } else {
      navigate("/roadmaps");
    }
  }, [navigate, locState.roadmapId]);

  const is404 =
    isError && error instanceof ApiError && error.status === 404;

  // Breadcrumbs
  const crumbs = [
    { label: "ロードマップ", onClick: () => navigate("/roadmaps") },
    ...(locState.topic && locState.roadmapId
      ? [
          {
            label: locState.topic,
            onClick: () => navigate(`/roadmaps/${locState.roadmapId}`),
          },
        ]
      : []),
    { label: "クイズ" },
  ];

  const headerAction =
    phase !== "summary" ? (
      <div className="flex items-center gap-2">
        <span className="text-xs text-muted-foreground">
          <Clock className="mr-1 inline h-[11px] w-[11px] align-middle" />
          進行中
        </span>
        <Button variant="outline" size="sm" disabled>
          <Pause className="h-3.5 w-3.5" />
          中断
        </Button>
      </div>
    ) : undefined;

  return (
    <>
      <AppShell crumbs={crumbs} action={headerAction}>
        {/* Loading */}
        {isLoading && (
          <div className="grid items-start gap-6 grid-cols-1 min-[1180px]:grid-cols-[1fr_288px]">
            <MainSkeleton />
            <SidebarSkeleton />
          </div>
        )}

        {/* Loaded */}
        {!isLoading && !isError && sessionState && (
          <>
            {phase !== "summary" && (
              <SessionHeader sessionState={sessionState} />
            )}

            {phase === "summary" ? (
              <SummaryPhase
                answers={sessionState.answers ?? []}
                onBack={handleBack}
              />
            ) : (
              <div className="grid items-start gap-6 grid-cols-1 min-[1180px]:grid-cols-[1fr_288px]">
                <div className="min-w-0 rounded-lg border border-border bg-card p-6">
                  {(phase === "question" || phase === "chat_response") &&
                    !sessionState.current_question_text && (
                    <div className="flex flex-col items-center gap-4 py-12 text-muted-foreground">
                      <span className="inline-block h-6 w-6 animate-[qs-spin_0.7s_linear_infinite] rounded-full border-2 border-[rgb(148_163_184/0.3)] border-t-[rgb(148_163_184/0.8)]" />
                      <span className="text-sm">問題を生成中…</span>
                    </div>
                  )}
                  {(phase === "question" || phase === "chat_response") &&
                    sessionState.current_question_text && (
                    <QuestionPhase
                      sessionState={sessionState}
                      isSubmitting={isSubmitting}
                      chatMessages={chatMessages}
                      answerDraft={answerDraft}
                      chatDraft={chatDraft}
                      onAnswerDraftChange={setAnswerDraft}
                      onChatDraftChange={setChatDraft}
                      onSubmitAnswer={(t) => void handleSubmitAnswer(t)}
                      onSubmitChat={(t) => void handleSubmitChat(t)}
                      onExplain={handleExplain}
                    />
                  )}
                  {phase === "feedback" && (
                    <FeedbackPhase
                      sessionState={sessionState}
                      onNext={handleNext}
                    />
                  )}
                  {phase === "explanation" && (
                    <ExplanationPhase
                      sessionState={sessionState}
                      explanationText={explanationText}
                      questionText={
                        questionSnapshot?.text ??
                        sessionState.current_question_text ??
                        ""
                      }
                      questionNumber={
                        questionSnapshot?.number ??
                        sessionState.total_questions_asked ??
                        1
                      }
                      onContinue={handleContinue}
                    />
                  )}
                </div>
                <SessionProgress
                  sessionState={sessionState}
                  phase={phase}
                />
              </div>
            )}
          </>
        )}

        {/* 404 */}
        {is404 && (
          <div className="mx-auto flex max-w-[480px] flex-col items-center px-6 pb-24 pt-14 text-center">
            <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-full border border-[rgb(244_63_94/0.25)] bg-[rgb(244_63_94/0.1)]">
              <SearchX className="h-8 w-8 text-[#fb7185]" />
            </div>
            <div className="mb-1.5 text-base font-semibold tracking-tight">
              セッションが見つかりません
            </div>
            <div className="mb-6 text-[13px] leading-relaxed text-muted-foreground">
              削除されたか、URLが間違っている可能性があります
            </div>
            <Button onClick={() => navigate("/roadmaps")}>
              <ArrowLeft className="h-4 w-4" />
              ロードマップへ
            </Button>
          </div>
        )}

        {/* Generic error */}
        {isError && !is404 && (
          <div className="rounded-lg border border-border bg-card p-2">
            <div className="flex flex-col items-center px-6 pb-16 pt-14 text-center text-muted-foreground">
              <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full border border-[rgb(244_63_94/0.25)] bg-[rgb(244_63_94/0.1)]">
                <AlertTriangle className="h-6 w-6 text-[#fb7185]" />
              </div>
              <div className="mb-1 text-sm font-semibold text-foreground">
                読み込みに失敗しました
              </div>
              <div className="mb-5 max-w-[360px] text-xs leading-relaxed">
                ネットワークを確認してから、もう一度お試しください。
              </div>
              <Button onClick={() => navigate(0)}>
                <RotateCcw className="h-4 w-4" />
                再読み込み
              </Button>
            </div>
          </div>
        )}
      </AppShell>

      {/* 503 Toast */}
      {showToast && <ErrorToast onClose={() => setShowToast(false)} />}
    </>
  );
}
