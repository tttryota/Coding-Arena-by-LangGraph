import { useEffect, useRef } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Database, SendHorizontal } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { MarkdownContent } from "@/components/common/markdown-content";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import {
  useAskSqlDojoQuestion,
  useSqlDojoSession,
  useSubmitSqlDojoAnswer,
} from "./use-sql-dojo";
import { useSqlDojoStore } from "./use-sql-dojo-store";

export function SqlDojoSessionPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const {
    session,
    result,
    phase,
    chatMessages,
    sqlDraft,
    chatDraft,
    isSubmitting,
    isQuestionSubmitting,
    addChatMessage,
    setSqlDraft,
    setChatDraft,
    setResult,
    setIsSubmitting,
    setIsQuestionSubmitting,
    setSession,
    reset,
  } = useSqlDojoStore();
  const submitMutation = useSubmitSqlDojoAnswer(sessionId ?? "");
  const questionMutation = useAskSqlDojoQuestion(sessionId ?? "");
  const needsRestore =
    sessionId != null && (!session || session.session_id !== sessionId);
  const { data: restored, isLoading: isRestoring } = useSqlDojoSession(
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
        theme_family: restored.theme_family,
        difficulty: restored.difficulty,
        dialect: restored.dialect,
        theme_title: restored.theme_title,
        business_domain: restored.business_domain,
        target_skill: restored.target_skill,
        problem_statement: restored.problem_statement,
        schema_markdown: restored.schema_markdown,
        sample_data_json: restored.sample_data_json,
        expected_focus: restored.expected_focus,
      });
      if (restored.status === "completed" && restored.score != null) {
        setResult({
          session_id: restored.session_id,
          score: restored.score,
          feedback: restored.feedback ?? "",
          rule_breakdown_json: restored.rule_breakdown_json ?? "[]",
          improvement_suggestions:
            restored.improvement_suggestions ?? "",
          reference_sql: restored.reference_sql ?? "",
        });
      }
    }
  }, [needsRestore, restored, sessionId, setSession, setResult]);

  if (!sessionId) {
    navigate("/sql-dojo");
    return null;
  }

  if (sessionMismatch || (!session && isRestoring)) {
    return (
      <AppShell crumbs={[{ label: "SQL道場" }, { label: "読み込み中..." }]}>
        <div className="animate-pulse space-y-4">
          <div className="h-8 w-64 rounded bg-muted" />
          <div className="h-96 rounded bg-muted" />
        </div>
      </AppShell>
    );
  }

  if (!session) {
    return (
      <AppShell crumbs={[{ label: "SQL道場" }, { label: "エラー" }]}>
        <div className="rounded-md bg-destructive/10 p-4 text-destructive">
          セッションが見つかりません。
          <Button
            variant="link"
            onClick={() => navigate("/sql-dojo")}
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
    if (!requestSessionId || !sqlDraft.trim()) return;
    setIsSubmitting(true);
    try {
      const res = await submitMutation.mutateAsync(sqlDraft);
      if (activeSessionIdRef.current !== requestSessionId) return;
      setResult(res);
    } catch {
      // handled by query state
    } finally {
      if (activeSessionIdRef.current === requestSessionId) {
        setIsSubmitting(false);
      }
    }
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
      addChatMessage({ role: "user", content: draft });
      addChatMessage({ role: "assistant", content: res.chat_response_text });
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
          { label: "SQL道場", onClick: () => navigate("/sql-dojo") },
          { label: session.theme_title },
          { label: "結果" },
        ]}
      >
        <SqlDojoResult result={result} session={session} />
      </AppShell>
    );
  }

  return (
    <AppShell
      crumbs={[
        { label: "SQL道場", onClick: () => navigate("/sql-dojo") },
        { label: session.theme_title },
      ]}
    >
      <div className="space-y-6">
        <div className="flex flex-wrap items-center gap-3">
          <Badge variant="secondary">{session.dialect}</Badge>
          <Badge variant="outline">{session.business_domain}</Badge>
          <Badge variant="outline">{session.target_skill}</Badge>
          <span className="font-semibold">{session.theme_title}</span>
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
            <div>
              <h4 className="mb-1 font-semibold text-sm">スキーマ</h4>
              <MarkdownContent content={session.schema_markdown} />
            </div>
            <div>
              <h4 className="mb-1 font-semibold text-sm">サンプルデータ規模</h4>
              <div className="max-w-full overflow-x-auto rounded bg-muted p-2">
                <pre className="text-xs">{session.sample_data_json}</pre>
              </div>
            </div>
            <div>
              <h4 className="mb-1 font-semibold text-sm">着眼点</h4>
              <div className="rounded bg-muted p-3 text-sm text-muted-foreground">
                {session.expected_focus}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>SQL</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <label htmlFor="sql-dojo-answer" className="font-semibold text-sm">
              SQL を入力
            </label>
            <Textarea
              id="sql-dojo-answer"
              aria-label="SQL を入力"
              value={sqlDraft}
              onChange={(e) => setSqlDraft(e.target.value)}
              placeholder="PostgreSQL で 1 文を書いてください"
              className="font-mono min-h-[260px]"
            />
            <Button
              onClick={handleSubmit}
              disabled={isSubmitting || !sqlDraft.trim()}
              className="w-full"
            >
              {isSubmitting ? "採点中..." : "提出"}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>問題への質問</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2">
              {chatMessages.length === 0 ? (
                <div className="text-sm text-muted-foreground">
                  完成 SQL ではなく、考え方のヒントを返します。
                </div>
              ) : (
                chatMessages.map((message, index) => (
                  <div
                    key={`${message.role}-${index}`}
                    className="rounded-lg border border-border bg-card p-3"
                  >
                    <div className="mb-1 text-xs font-semibold text-muted-foreground">
                      {message.role === "user" ? "あなた" : "ヒント"}
                    </div>
                    <div className="text-sm whitespace-pre-wrap">{message.content}</div>
                  </div>
                ))
              )}
            </div>
            <label htmlFor="sql-dojo-question" className="font-semibold text-sm">
              ヒントを質問
            </label>
            <Textarea
              id="sql-dojo-question"
              aria-label="ヒントを質問"
              value={chatDraft}
              onChange={(e) => setChatDraft(e.target.value)}
              placeholder="JOIN の組み方、どの句から書くべきか、インデックス観点などを質問できます"
            />
            <Button
              variant="outline"
              onClick={handleAskQuestion}
              disabled={isQuestionSubmitting || !chatDraft.trim()}
              className="w-full"
            >
              <SendHorizontal className="mr-2 h-4 w-4" />
              {isQuestionSubmitting ? "質問中..." : "質問する"}
            </Button>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}

function SqlDojoResult({
  result,
  session,
}: {
  result: {
    score: number;
    feedback: string;
    rule_breakdown_json: string;
    improvement_suggestions: string;
    reference_sql: string;
  };
  session: { theme_title: string };
}) {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Database className="h-5 w-5 text-cyan-400" />
        <h1 className="text-2xl font-bold">結果: {session.theme_title}</h1>
        <Badge variant="secondary">{result.score} 点</Badge>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>講評</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded bg-muted p-3 text-sm whitespace-pre-wrap">
            {result.feedback}
          </div>
          <div>
            <h4 className="mb-1 font-semibold text-sm">改善提案</h4>
            <div className="rounded bg-muted p-3 text-sm whitespace-pre-wrap">
              {result.improvement_suggestions}
            </div>
          </div>
          <div>
            <h4 className="mb-1 font-semibold text-sm">ルール判定</h4>
            <div className="max-w-full overflow-x-auto rounded bg-muted p-3">
              <pre className="text-xs">{result.rule_breakdown_json}</pre>
            </div>
          </div>
          {result.reference_sql && (
            <div>
              <h4 className="mb-1 font-semibold text-sm">参考 SQL</h4>
              <div className="max-w-full overflow-x-auto rounded bg-muted p-3">
                <pre className="text-xs">{result.reference_sql}</pre>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
