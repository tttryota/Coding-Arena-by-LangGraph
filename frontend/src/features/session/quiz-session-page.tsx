import { useState, useEffect, useCallback, useRef } from "react";
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
import { useStartPractice } from "./use-start-practice";
import { LearningPhase } from "./learning-phase";
import { LecturePhase } from "./lecture-phase";
import { useQuizSessionStore } from "./use-quiz-session-store";
import { SessionHeader } from "./session-header";
import { QuestionPhase } from "./question-phase";
import { FeedbackPhase } from "./feedback-phase";
import { ExplanationPhase } from "./explanation-phase";
import { SummaryPhase } from "./summary-phase";
import { SessionProgress } from "./session-progress";
import { MainSkeleton, SidebarSkeleton } from "./session-skeleton";
import { ErrorToast } from "./error-toast";
import type {
  SessionState,
  CodingSessionStateDTO,
  ConfirmationPoint,
} from "@/types/api";

/** Navigation state passed from roadmap detail page */
interface LocationState {
  topic?: string;
  roadmapId?: string;
}

/** Type guard: CodingSessionStateDTO has lecture_phase_active or current_format */
function isCodingState(
  state: SessionState | CodingSessionStateDTO,
): state is CodingSessionStateDTO {
  return "lecture_phase_active" in state || "lecture_content" in state || "current_format" in state;
}

/** Adapt CodingSessionStateDTO to SessionState-compatible shape for shared components */
function adaptCodingState(cs: CodingSessionStateDTO): SessionState {
  const cps: ConfirmationPoint[] | undefined = cs.confirmation_points?.map((cp) => ({
    id: cp.id,
    content: cp.content,
    format: "knowledge_and_practice",
  }));
  return {
    session_id: cs.session_id,
    roadmap_item_id: cs.roadmap_item_id,
    roadmap_item_level: cs.roadmap_item_level,
    roadmap_item_title: cs.roadmap_item_title,
    roadmap_item_description: cs.roadmap_item_description,
    is_resumed: cs.is_resumed,
    current_question_text: cs.current_question_text,
    current_answer_type: "code",
    total_questions_asked: cs.total_questions_asked,
    confirmation_points: cps,
    current_point_index: cs.current_point_index,
  };
}

export function QuizSessionPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const locState = (location.state ?? {}) as LocationState;

  const { data, isLoading, isError, error } = useSession(sessionId ?? "");
  const submitInput = useSubmitInput(sessionId ?? "");
  const startPractice = useStartPractice(sessionId ?? "");

  const {
    phase,
    sessionType,
    sessionState,
    codingState,
    chatMessages,
    lectureChatMessages,
    answerDraft,
    chatDraft,
    isSubmitting,
    explanationText,
    questionSnapshot,
    setPhase,
    setSessionType,
    setSessionState,
    setCodingState,
    addChatMessage,
    addLectureChatMessage,
    setAnswerDraft,
    setChatDraft,
    setIsSubmitting,
    setExplanationText,
    setLastChatResponse,
    setQuestionSnapshot,
    codingFeedbackSnapshot,
    setCodingFeedbackSnapshot,
    reset,
  } = useQuizSessionStore();

  const [showToast, setShowToast] = useState(false);
  const hasHydratedRef = useRef(false);

  // Reset store on unmount or sessionId change
  useEffect(() => {
    return () => {
      hasHydratedRef.current = false;
      reset();
    };
  }, [sessionId, reset]);

  // Initialize sessionState from API response
  useEffect(() => {
    if (!data || hasHydratedRef.current) return;

    const gs = data.graph_state;
    if (!gs) return;

    hasHydratedRef.current = true;

    if (isCodingState(gs)) {
      // Coding session
      setSessionType("coding");
      setCodingState(gs);
      setSessionState(adaptCodingState(gs));

      if (gs.next_action === "complete") {
        setPhase("summary");
      } else if (gs.lecture_phase_active !== false) {
        setPhase("lecture");
      } else if (gs.current_question_text) {
        setPhase("question");
      }
    } else {
      // Quiz session
      setSessionType("quiz");
      setSessionState(gs);

      if (data.session?.status === "completed") {
        setPhase("summary");
      } else if (gs.topic_overview && (!gs.answers || gs.answers.length === 0)) {
        setPhase("learning");
      }
    }
  }, [data, setSessionState, setCodingState, setSessionType, setPhase]);

  const isCoding = sessionType === "coding";

  // --- Quiz handlers ---

  const handleSubmitAnswer = useCallback(
    async (text: string) => {
      if (!sessionId || isSubmitting) return;
      if (!isCoding && sessionState?.current_question_text) {
        setQuestionSnapshot({
          text: sessionState.current_question_text,
          number: sessionState.total_questions_asked ?? 1,
          cpIndex: sessionState.current_point_index ?? 0,
        });
      }
      if (isCoding && codingState) {
        setCodingFeedbackSnapshot({
          questionText: codingState.current_question_text ?? "",
          questionNumber: codingState.total_questions_asked ?? 1,
          format: codingState.current_format,
          cpIndex: codingState.current_point_index ?? 0,
        });
      }
      setIsSubmitting(true);
      try {
        const result = await submitInput.mutateAsync({
          user_input: text,
          input_source: "form",
        });
        if (isCoding && isCodingState(result)) {
          setCodingState(result);
          setSessionState(adaptCodingState(result));
          setAnswerDraft("");
          setPhase("feedback");
        } else if (!isCoding && !isCodingState(result)) {
          setSessionState(result);
          setAnswerDraft("");
          if (result.input_type === "answer") {
            setPhase("feedback");
          }
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
      isCoding,
      isSubmitting,
      sessionState,
      codingState,
      submitInput,
      setSessionState,
      setCodingState,
      setAnswerDraft,
      setPhase,
      setIsSubmitting,
      setQuestionSnapshot,
      setCodingFeedbackSnapshot,
    ],
  );

  const handleSubmitChat = useCallback(
    async (text: string) => {
      if (!sessionId || isSubmitting) return;
      if (!isCoding && sessionState?.current_question_text) {
        setQuestionSnapshot({
          text: sessionState.current_question_text,
          number: sessionState.total_questions_asked ?? 1,
          cpIndex: sessionState.current_point_index ?? 0,
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
        if (isCoding && isCodingState(result)) {
          setCodingState(result);
          setSessionState(adaptCodingState(result));
          if (result.chat_response_text) {
            addChatMessage({ role: "assistant", content: result.chat_response_text });
          }
          setPhase("question");
        } else if (!isCoding && !isCodingState(result)) {
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
      isCoding,
      isSubmitting,
      sessionState,
      submitInput,
      setSessionState,
      setCodingState,
      setChatDraft,
      setPhase,
      setIsSubmitting,
      setExplanationText,
      setLastChatResponse,
      addChatMessage,
      setQuestionSnapshot,
    ],
  );

  // --- Lecture handlers ---

  const handleLectureSendChat = useCallback(
    async (text: string) => {
      if (!sessionId || isSubmitting) return;
      setIsSubmitting(true);
      addLectureChatMessage({ role: "user", content: text });
      try {
        const result = await submitInput.mutateAsync({
          user_input: text,
          input_source: "chat",
        });
        if (isCodingState(result)) {
          setCodingState(result);
          setSessionState(adaptCodingState(result));
          if (result.chat_response_text) {
            addLectureChatMessage({ role: "assistant", content: result.chat_response_text });
          }
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
      submitInput,
      setCodingState,
      setSessionState,
      addLectureChatMessage,
      setIsSubmitting,
    ],
  );

  const handleStartPractice = useCallback(async () => {
    if (!sessionId || isSubmitting) return;
    setIsSubmitting(true);
    try {
      const result = await startPractice.mutateAsync();
      // Build a partial CodingSessionStateDTO from practice start response + existing coding state
      const updated: CodingSessionStateDTO = {
        ...(codingState ?? ({} as CodingSessionStateDTO)),
        session_id: result.session_id,
        lecture_phase_active: false,
        confirmation_points: result.confirmation_points,
        current_question_text: result.current_question_text,
        current_example_code: result.current_example_code,
        current_format: result.current_format,
        current_point_index: result.current_point_index ?? 0,
        total_questions_asked: result.total_questions_asked ?? 1,
      };
      setCodingState(updated);
      setSessionState(adaptCodingState(updated));
      setPhase("question");
    } catch (err) {
      if (err instanceof ApiError && err.status === 503) {
        setShowToast(true);
      }
    } finally {
      setIsSubmitting(false);
    }
  }, [
    sessionId,
    isSubmitting,
    codingState,
    startPractice,
    setCodingState,
    setSessionState,
    setPhase,
    setIsSubmitting,
  ]);

  // --- Navigation handlers ---

  const handleExplain = useCallback(() => {
    void handleSubmitChat("解説してください");
  }, [handleSubmitChat]);

  const handleNext = useCallback(() => {
    if (isCoding) {
      if (codingState?.next_action === "complete") {
        setPhase("summary");
      } else {
        setPhase("question");
        setAnswerDraft("");
      }
    } else {
      if (sessionState?.next_action === "complete") {
        setPhase("summary");
      } else {
        setPhase("question");
        setAnswerDraft("");
      }
    }
  }, [isCoding, codingState, sessionState, setPhase, setAnswerDraft]);

  const handleContinue = useCallback(() => {
    setPhase("question");
    setAnswerDraft("");
  }, [setPhase, setAnswerDraft]);

  const handleStartTest = useCallback(() => {
    setPhase("question");
  }, [setPhase]);

  const handleBack = useCallback(() => {
    if (locState.roadmapId) {
      navigate(`/roadmaps/${locState.roadmapId}`);
    } else {
      navigate("/roadmaps");
    }
  }, [navigate, locState.roadmapId]);

  // --- Render conditions ---

  const is404 =
    isError && error instanceof ApiError && error.status === 404;
  const hasRecoverableData = !isLoading && !isError && !!data;
  const showRestoreError = hasRecoverableData && !data.graph_state;
  const showLoadedContent = !isLoading && !isError && !!sessionState && !showRestoreError;
  const isInteractivePhase =
    phase !== "learning" && phase !== "lecture" && phase !== "summary";
  const isQuestionPhase = phase === "question" || phase === "chat_response";
  const isQuestionPending =
    isQuestionPhase && !sessionState?.current_question_text;
  const showQuestionPhase =
    isQuestionPhase && !!sessionState?.current_question_text;
  const explanationQuestionText =
    questionSnapshot?.text ?? sessionState?.current_question_text ?? "";
  const explanationQuestionNumber =
    questionSnapshot?.number ?? sessionState?.total_questions_asked ?? 1;

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
    { label: isCoding ? "コーディング" : "クイズ" },
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

        {/* graph_state 欠落 */}
        {showRestoreError && (
          <div className="mx-auto flex max-w-[480px] flex-col items-center px-6 pb-24 pt-14 text-center">
            <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-full border border-[rgb(244_63_94/0.25)] bg-[rgb(244_63_94/0.1)]">
              <AlertTriangle className="h-8 w-8 text-[#fb7185]" />
            </div>
            <div className="mb-1.5 text-base font-semibold tracking-tight">
              セッションの状態を復元できません
            </div>
            <div className="mb-6 text-[13px] leading-relaxed text-muted-foreground">
              サーバーが再起動された可能性があります。新しいセッションを開始してください。
            </div>
            <Button onClick={handleBack}>
              <ArrowLeft className="h-4 w-4" />
              ロードマップへ
            </Button>
          </div>
        )}

        {/* Loaded */}
        {showLoadedContent && (
          <>
            {/* Lecture phase (coding sessions) */}
            {phase === "lecture" && codingState && (
              <div className="mx-auto max-w-[720px]">
                <h1 className="mb-2 text-xl font-semibold tracking-tight">
                  {sessionState.roadmap_item_title}
                </h1>
                <p className="mb-6 text-sm text-muted-foreground">
                  {sessionState.roadmap_item_description}
                </p>
                <LecturePhase
                  lectureContent={codingState.lecture_content ?? ""}
                  chatMessages={lectureChatMessages}
                  onSendChat={handleLectureSendChat}
                  onStartPractice={() => void handleStartPractice()}
                  isSubmitting={isSubmitting}
                />
              </div>
            )}

            {/* Learning phase (quiz sessions) */}
            {phase === "learning" && !isCoding && (
              <LearningPhase
                sessionState={sessionState}
                onStartTest={handleStartTest}
              />
            )}

            {/* Summary phase */}
            {phase === "summary" && (
              <SummaryPhase
                answers={isCoding ? [] : (sessionState.answers ?? [])}
                onBack={handleBack}
                codingScore={isCoding ? codingState?.current_score : undefined}
                codingTotalQuestions={isCoding ? (codingState?.total_questions_asked ?? 0) : undefined}
              />
            )}

            {/* Question/Feedback/Explanation phases */}
            {isInteractivePhase && (
              <>
                <SessionHeader sessionState={sessionState} />
                <div className="grid items-start gap-6 grid-cols-1 min-[1180px]:grid-cols-[1fr_288px]">
                  <div className="min-w-0 rounded-lg border border-border bg-card p-6">
                    {isQuestionPending && (
                      <div className="flex flex-col items-center gap-4 py-12 text-muted-foreground">
                        <span className="inline-block h-6 w-6 animate-[qs-spin_0.7s_linear_infinite] rounded-full border-2 border-[rgb(148_163_184/0.3)] border-t-[rgb(148_163_184/0.8)]" />
                        <span className="text-sm">問題を生成中...</span>
                      </div>
                    )}
                    {showQuestionPhase && (
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
                        exampleCode={isCoding ? codingState?.current_example_code : undefined}
                        currentFormat={isCoding ? codingState?.current_format : undefined}
                        hideExplainButton={isCoding}
                      />
                    )}
                    {phase === "feedback" && (
                      <FeedbackPhase
                        sessionState={sessionState}
                        onNext={handleNext}
                        codingScore={isCoding ? codingState?.current_score : undefined}
                        codingFeedback={isCoding ? codingState?.current_feedback : undefined}
                        codingNextAction={isCoding ? codingState?.next_action : undefined}
                        codingFormat={isCoding ? codingFeedbackSnapshot?.format : undefined}
                        codingQuestionText={isCoding ? codingFeedbackSnapshot?.questionText : undefined}
                        codingQuestionNumber={isCoding ? codingFeedbackSnapshot?.questionNumber : undefined}
                        snapshotCpIndex={isCoding
                          ? codingFeedbackSnapshot?.cpIndex
                          : questionSnapshot?.cpIndex}
                      />
                    )}
                    {phase === "explanation" && !isCoding && (
                      <ExplanationPhase
                        sessionState={sessionState}
                        explanationText={explanationText}
                        questionText={explanationQuestionText}
                        questionNumber={explanationQuestionNumber}
                        onContinue={handleContinue}
                      />
                    )}
                  </div>
                  <SessionProgress
                    sessionState={sessionState}
                    phase={phase}
                    isCoding={isCoding}
                    codingFormat={isCoding
                      ? (phase === "feedback" ? codingFeedbackSnapshot?.format : codingState?.current_format)
                      : undefined}
                    codingScore={isCoding ? codingState?.current_score : undefined}
                    feedbackQuestionNumber={
                      phase === "feedback"
                        ? (isCoding ? codingFeedbackSnapshot?.questionNumber : questionSnapshot?.number)
                        : undefined
                    }
                    feedbackCpIndex={
                      phase === "feedback"
                        ? (isCoding ? codingFeedbackSnapshot?.cpIndex : questionSnapshot?.cpIndex)
                        : undefined
                    }
                    feedbackQuestionText={
                      phase === "feedback"
                        ? (isCoding ? codingFeedbackSnapshot?.questionText : questionSnapshot?.text)
                        : undefined
                    }
                  />
                </div>
              </>
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
