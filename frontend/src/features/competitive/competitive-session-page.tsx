import { useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { AppShell } from "@/components/layout/app-shell";
import { useCompetitiveStore } from "./use-competitive-store";
import { useSubmitAnswer, useCompetitiveSession } from "./use-competitive";

export function CompetitiveSessionPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const {
    session,
    result,
    phase,
    codeDraft,
    isSubmitting,
    setCodeDraft,
    setResult,
    setIsSubmitting,
    setSession,
  } = useCompetitiveStore();
  const submitMutation = useSubmitAnswer(sessionId ?? "");
  const { data: restored, isLoading: isRestoring } = useCompetitiveSession(
    !session && sessionId ? sessionId : "",
  );

  useEffect(() => {
    if (!session && restored && sessionId) {
      setSession({
        session_id: restored.session_id,
        theme_id: restored.theme_id,
        theme_label: restored.theme_label,
        theme_category: restored.theme_category,
        programming_language: restored.programming_language as "python" | "typescript",
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
        });
      }
    }
  }, [session, restored, sessionId, setSession, setResult]);

  if (!sessionId) {
    navigate("/algorithm-quiz");
    return null;
  }

  if (!session && isRestoring) {
    return (
      <AppShell crumbs={[{ label: "競プロクイズ" }, { label: "読み込み中..." }]}>
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
    if (!codeDraft.trim()) return;
    setIsSubmitting(true);
    try {
      const res = await submitMutation.mutateAsync(codeDraft);
      setResult(res);
    } catch {
      // TanStack Query handles error state
    } finally {
      setIsSubmitting(false);
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
            <p className="whitespace-pre-wrap">{session.problem_statement}</p>

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
              placeholder={`# ${session.programming_language} で解答を書いてください`}
              className="font-mono min-h-[200px]"
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
            <p className="whitespace-pre-wrap">{result.feedback}</p>
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
            <p className="whitespace-pre-wrap">
              {result.improvement_suggestions}
            </p>
          </div>
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
