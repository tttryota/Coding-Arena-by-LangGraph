import { useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { MessageCircle, SendHorizontal } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { AppShell } from "@/components/layout/app-shell";
import { MarkdownContent } from "@/components/common/markdown-content";
import {
  applyTextareaIndent,
  restoreTextareaSelection,
} from "@/lib/textarea-indent";
import { useCompetitiveStore } from "./use-competitive-store";
import {
  useAskQuestion,
  useSubmitAnswer,
  useCompetitiveSession,
} from "./use-competitive";
import type { CompetitiveChatMessage } from "@/types/api";

function codePlaceholder(language: string) {
  const placeholders: Record<string, string> = {
    python: "# Python で解答を書いてください",
    typescript: "// TypeScript で解答を書いてください",
  };
  return placeholders[language] ?? `// ${language} で解答を書いてください`;
}

export function CompetitiveSessionPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const {
    session,
    result,
    phase,
    chatMessages,
    codeDraft,
    chatDraft,
    isSubmitting,
    isQuestionSubmitting,
    addChatMessage,
    setCodeDraft,
    setChatDraft,
    setResult,
    setIsSubmitting,
    setIsQuestionSubmitting,
    setSession,
    reset,
  } = useCompetitiveStore();
  const submitMutation = useSubmitAnswer(sessionId ?? "");
  const questionMutation = useAskQuestion(sessionId ?? "");
  const needsRestore =
    sessionId != null && (!session || session.session_id !== sessionId);
  const { data: restored, isLoading: isRestoring } = useCompetitiveSession(
    needsRestore ? sessionId : "",
  );
  const activeSessionIdRef = useRef<string | null>(sessionId ?? null);

  const sessionMismatch =
    session != null && sessionId != null && session.session_id !== sessionId;

  useEffect(() => {
    activeSessionIdRef.current = sessionId ?? null;
  }, [sessionId]);

  useEffect(() => {
    if (sessionMismatch) {
      reset();
    }
  }, [sessionMismatch, reset]);

  useEffect(() => {
    if (needsRestore && restored && sessionId) {
      setSession({
        session_id: restored.session_id,
        theme_id: restored.theme_id,
        theme_label: restored.theme_label,
        theme_category: restored.theme_category,
        programming_language: restored.programming_language,
        problem_statement: restored.problem_statement,
        input_format: restored.input_format,
        output_format: restored.output_format,
        constraints: restored.constraints,
        examples: restored.examples,
      });
      if (restored.status === "completed" && restored.score != null) {
        setResult({
          session_id: restored.session_id,
          score: restored.score,
          feedback: restored.feedback ?? "",
          time_complexity: restored.time_complexity ?? "",
          space_complexity: restored.space_complexity ?? "",
          improvement_suggestions: restored.improvement_suggestions ?? "",
          rubric_scores_json: restored.rubric_scores_json ?? "[]",
          reference_solution: "",
        });
      }
    }
  }, [needsRestore, restored, sessionId, setSession, setResult]);

  if (!sessionId) {
    navigate("/algorithm-quiz");
    return null;
  }

  if (sessionMismatch || (!session && isRestoring)) {
    return (
      <AppShell
        crumbs={[{ label: "競プロクイズ" }, { label: "読み込み中..." }]}
      >
        <div className="animate-pulse space-y-4">
          <div className="h-8 w-64 rounded bg-muted" />
          <div className="h-96 rounded bg-muted" />
        </div>
      </AppShell>
    );
  }

  if (!session) {
    return (
      <AppShell crumbs={[{ label: "競プロクイズ" }, { label: "エラー" }]}>
        <div className="rounded-md bg-destructive/10 p-4 text-destructive">
          セッションが見つかりません。
          <Button
            variant="link"
            onClick={() => navigate("/algorithm-quiz")}
            className="ml-2"
          >
            一覧に戻る
          </Button>
        </div>
      </AppShell>
    );
  }

  const handleSubmit = async () => {
    const requestSessionId = sessionId ?? null;
    if (!requestSessionId || !codeDraft.trim()) return;
    setIsSubmitting(true);
    try {
      const res = await submitMutation.mutateAsync(codeDraft);
      if (activeSessionIdRef.current !== requestSessionId) return;
      setResult(res);
    } catch {
      // TanStack Query handles error state
    } finally {
      if (activeSessionIdRef.current === requestSessionId) {
        setIsSubmitting(false);
      }
    }
  };

  const handleCodeKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key !== "Tab") return;
    e.preventDefault();
    const nextState = applyTextareaIndent(
      codeDraft,
      e.currentTarget.selectionStart,
      e.currentTarget.selectionEnd,
      { outdent: e.shiftKey },
    );
    setCodeDraft(nextState.value);
    restoreTextareaSelection(e.currentTarget, nextState);
  };

  const handleAskQuestion = async () => {
    const requestSessionId = sessionId ?? null;
    const draft = chatDraft;
    if (!requestSessionId || !draft.trim()) return;
    setIsQuestionSubmitting(true);
    try {
      const res = await questionMutation.mutateAsync({
        user_input: draft,
        history: chatMessages,
      });
      if (activeSessionIdRef.current !== requestSessionId) return;
      setChatDraft("");
      addChatMessage({
        role: "user",
        content: draft,
      });
      addChatMessage({
        role: "assistant",
        content: res.chat_response_text,
      });
    } catch {
      if (activeSessionIdRef.current !== requestSessionId) return;
      setChatDraft(draft);
    } finally {
      if (activeSessionIdRef.current === requestSessionId) {
        setIsQuestionSubmitting(false);
      }
    }
  };

  if (phase === "result" && result) {
    return (
      <AppShell
        crumbs={[
          { label: "競プロクイズ", onClick: () => navigate("/algorithm-quiz") },
          { label: session.theme_label },
          { label: "結果" },
        ]}
      >
        <CompetitiveResult result={result} session={session} />
      </AppShell>
    );
  }

  return (
    <AppShell
      crumbs={[
        { label: "競プロクイズ", onClick: () => navigate("/algorithm-quiz") },
        { label: session.theme_label },
      ]}
    >
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <Badge variant="secondary">{session.programming_language}</Badge>
          <Badge variant="outline">{session.theme_category}</Badge>
          <span className="font-semibold">{session.theme_label}</span>
        </div>

        {submitMutation.isError && (
          <div className="rounded-md bg-destructive/10 p-4 text-destructive">
            提出に失敗しました。もう一度お試しください。
          </div>
        )}

        <Card>
          <CardHeader>
            <CardTitle>問題</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <MarkdownContent content={session.problem_statement} />

            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <h4 className="font-semibold mb-1">入力形式</h4>
                <pre className="bg-muted p-2 rounded text-xs">
                  {session.input_format}
                </pre>
              </div>
              <div>
                <h4 className="font-semibold mb-1">出力形式</h4>
                <pre className="bg-muted p-2 rounded text-xs">
                  {session.output_format}
                </pre>
              </div>
            </div>

            <div>
              <h4 className="font-semibold mb-1 text-sm">制約</h4>
              <pre className="bg-muted p-2 rounded text-xs">
                {session.constraints}
              </pre>
            </div>

            <div>
              <h4 className="font-semibold mb-1 text-sm">入出力例</h4>
              {session.examples.map((ex, i) => (
                <div key={i} className="grid grid-cols-2 gap-2 mb-2">
                  <pre className="bg-muted p-2 rounded text-xs">
                    入力: {ex.input}
                  </pre>
                  <pre className="bg-muted p-2 rounded text-xs">
                    出力: {ex.output}
                  </pre>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>解答コード</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Textarea
              value={codeDraft}
              onChange={(e) => setCodeDraft(e.target.value)}
              onKeyDown={handleCodeKeyDown}
              placeholder={codePlaceholder(session.programming_language)}
              className="font-mono min-h-[320px] [tab-size:2]"
            />
            <Button
              onClick={handleSubmit}
              disabled={isSubmitting || !codeDraft.trim()}
              className="w-full"
            >
              {isSubmitting ? "採点中..." : "提出"}
            </Button>
          </CardContent>
        </Card>

        <CompetitiveQuestionPanel
          chatMessages={chatMessages}
          chatDraft={chatDraft}
          isSubmitting={isQuestionSubmitting}
          onChatDraftChange={setChatDraft}
          onSubmit={handleAskQuestion}
        />
      </div>
    </AppShell>
  );
}

function CompetitiveResult({
  result,
  session,
}: {
  result: {
    score: number;
    feedback: string;
    time_complexity: string;
    space_complexity: string;
    improvement_suggestions: string;
    rubric_scores_json: string;
    reference_solution: string;
  };
  session: { theme_label: string };
}) {
  const navigate = useNavigate();
  const { reset } = useCompetitiveStore();

  const rubricScores = (() => {
    try {
      return JSON.parse(result.rubric_scores_json) as Array<{
        criterion: string;
        points_awarded: number;
        points_max: number;
      }>;
    } catch {
      return [];
    }
  })();

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">結果: {session.theme_label}</h1>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-3">
            スコア
            <Badge
              variant={result.score >= 70 ? "default" : "destructive"}
              className="text-lg px-3 py-1"
            >
              {result.score} / 100
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h4 className="font-semibold mb-1">フィードバック</h4>
            <MarkdownContent content={result.feedback} />
          </div>

          {rubricScores.length > 0 && (
            <div>
              <h4 className="font-semibold mb-2">採点内訳</h4>
              <div className="space-y-1">
                {rubricScores.map((rs, i) => (
                  <div key={i} className="flex justify-between text-sm">
                    <span>{rs.criterion}</span>
                    <span>
                      {rs.points_awarded} / {rs.points_max}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <h4 className="font-semibold">時間計算量</h4>
              <p>{result.time_complexity}</p>
            </div>
            <div>
              <h4 className="font-semibold">空間計算量</h4>
              <p>{result.space_complexity}</p>
            </div>
          </div>

          <div>
            <h4 className="font-semibold mb-1">改善提案</h4>
            <MarkdownContent content={result.improvement_suggestions} />
          </div>

          {result.reference_solution && (
            <div>
              <h4 className="font-semibold mb-2">正解コード</h4>
              <pre className="overflow-x-auto rounded-md bg-[#0b1220] px-4 py-3.5 font-mono text-[13px] leading-relaxed text-[#e2e8f0]">
                {result.reference_solution}
              </pre>
            </div>
          )}
        </CardContent>
      </Card>

      <Button
        onClick={() => {
          reset();
          navigate("/algorithm-quiz");
        }}
        className="w-full"
      >
        別の問題に挑戦
      </Button>
    </div>
  );
}

function CompetitiveQuestionPanel({
  chatMessages,
  chatDraft,
  isSubmitting,
  onChatDraftChange,
  onSubmit,
}: {
  chatMessages: CompetitiveChatMessage[];
  chatDraft: string;
  isSubmitting: boolean;
  onChatDraftChange: (value: string) => void;
  onSubmit: () => void;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MessageCircle className="h-4 w-4" />
          問題への質問
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm text-muted-foreground">
          提出前はヒント中心の応答です。正解コードや完成済みの解法は返しません。
        </p>

        {chatMessages.length > 0 && (
          <div className="space-y-2 rounded-md border border-border bg-muted/20 p-3">
            {chatMessages.map((message, index) => (
              <div key={index} className="space-y-1">
                <div className="text-xs font-semibold text-muted-foreground">
                  {message.role === "user" ? "あなた" : "アシスタント"}
                </div>
                <div className="rounded-md bg-background px-3 py-2 text-sm">
                  <MarkdownContent content={message.content} />
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="flex items-start gap-2">
          <Textarea
            value={chatDraft}
            onChange={(e) => onChatDraftChange(e.target.value)}
            placeholder="制約の見方、考える順番、計算量の見積もりなどを質問できます"
            className="min-h-[120px] resize-y"
            disabled={isSubmitting}
          />
          <Button
            type="button"
            onClick={onSubmit}
            disabled={isSubmitting || !chatDraft.trim()}
            className="shrink-0"
          >
            <SendHorizontal className="h-4 w-4" />
            {isSubmitting ? "送信中..." : "質問する"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
