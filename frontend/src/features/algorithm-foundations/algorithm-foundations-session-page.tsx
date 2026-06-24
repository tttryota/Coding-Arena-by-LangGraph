import { useMemo, useState } from "react";
import type { KeyboardEvent } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { AlertTriangle, Target } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { MarkdownContent } from "@/components/common/markdown-content";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import {
  applyTextareaIndent,
  restoreTextareaSelection,
} from "@/lib/textarea-indent";
import {
  useAlgorithmFoundationSession,
  useSubmitAlgorithmFoundationAnswer,
} from "./use-algorithm-foundations";
import type {
  AlgorithmFoundationAnswerResponse,
  AlgorithmFoundationSessionResponse,
  AlgorithmFoundationUnitKind,
} from "@/types/api";

function unitKindLabel(kind: AlgorithmFoundationUnitKind) {
  return kind === "integration" ? "総合演習" : "基礎";
}

function resultFromSession(
  session: AlgorithmFoundationSessionResponse,
): AlgorithmFoundationAnswerResponse | null {
  if (session.status !== "completed" || session.score == null) {
    return null;
  }
  return {
    session_id: session.session_id,
    score: session.score,
    feedback: session.feedback ?? "",
    time_complexity: session.time_complexity ?? "",
    space_complexity: session.space_complexity ?? "",
    improvement_suggestions: session.improvement_suggestions ?? "",
    rubric_scores_json: session.rubric_scores_json ?? "[]",
    reference_solution: session.reference_solution ?? "",
  };
}

export function AlgorithmFoundationsSessionPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();

  if (!sessionId) {
    navigate("/algorithm-foundations");
    return null;
  }

  return (
    <AlgorithmFoundationsSessionPageInner
      key={sessionId}
      sessionId={sessionId}
    />
  );
}

function AlgorithmFoundationsSessionPageInner({
  sessionId,
}: {
  sessionId: string;
}) {
  const navigate = useNavigate();
  const sessionQuery = useAlgorithmFoundationSession(sessionId ?? "");
  const submitMutation = useSubmitAlgorithmFoundationAnswer(sessionId ?? "");
  const [draft, setDraft] = useState("");
  const [resultOverride, setResultOverride] =
    useState<AlgorithmFoundationAnswerResponse | null>(null);
  const session = sessionQuery.data;
  const result =
    session != null ? resultOverride ?? resultFromSession(session) : null;

  if (sessionQuery.isLoading) {
    return (
      <AppShell crumbs={[{ label: "競プロうさぎ" }, { label: "読み込み中..." }]}>
        <div className="animate-pulse space-y-4">
          <div className="h-8 w-64 rounded bg-muted" />
          <div className="h-96 rounded bg-muted" />
        </div>
      </AppShell>
    );
  }

  if (sessionQuery.isError || !sessionQuery.data) {
    return (
      <AppShell crumbs={[{ label: "競プロうさぎ" }, { label: "エラー" }]}>
        <div className="rounded-md bg-destructive/10 p-4 text-destructive">
          セッションが見つかりません。
          <Button
            variant="link"
            onClick={() => navigate("/algorithm-foundations")}
            className="ml-2"
          >
            一覧に戻る
          </Button>
        </div>
      </AppShell>
    );
  }

  if (!session) {
    return null;
  }

  const handleSubmit = async () => {
    if (!draft.trim()) return;
    try {
      const response = await submitMutation.mutateAsync(draft);
      setResultOverride(response);
    } catch {
      // handled by query state
    }
  };

  const handleCodeKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key !== "Tab") return;
    event.preventDefault();
    const nextState = applyTextareaIndent(
      draft,
      event.currentTarget.selectionStart,
      event.currentTarget.selectionEnd,
      { outdent: event.shiftKey },
    );
    setDraft(nextState.value);
    restoreTextareaSelection(event.currentTarget, nextState);
  };

  if (result) {
    return (
      <AppShell
        crumbs={[
          { label: "競プロうさぎ", onClick: () => navigate("/algorithm-foundations") },
          { label: session.unit_title },
          { label: "結果" },
        ]}
      >
        <AlgorithmFoundationsResult
          result={result}
          session={session}
          onBack={() => navigate("/algorithm-foundations")}
        />
      </AppShell>
    );
  }

  return (
    <AppShell
      crumbs={[
        { label: "競プロうさぎ", onClick: () => navigate("/algorithm-foundations") },
        { label: session.unit_title },
      ]}
    >
      <div className="space-y-6">
        <div className="flex flex-wrap items-center gap-3">
          <Badge variant="secondary">{session.programming_language}</Badge>
          <Badge variant="outline">{session.group_title}</Badge>
          <Badge variant="outline">{unitKindLabel(session.unit_kind)}</Badge>
          {session.recommended && <Badge>推奨</Badge>}
          <span className="font-semibold">{session.unit_title}</span>
        </div>

        {session.has_unmet_prerequisites && (
          <div className="flex items-start gap-2 rounded-md border border-amber-400/30 bg-amber-400/10 p-4 text-amber-100">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            <div className="space-y-1 text-sm">
              <div className="font-medium">前提未達のまま開始しています</div>
              <div>
                問題は解けますが、先に {session.prerequisite_titles.join(" / ")}
                を触れておくと理解しやすくなります。
              </div>
            </div>
          </div>
        )}

        {submitMutation.isError && (
          <div className="rounded-md bg-destructive/10 p-4 text-destructive">
            提出に失敗しました。もう一度お試しください。
          </div>
        )}

        <div className="grid gap-4 lg:grid-cols-[minmax(0,1.5fr)_minmax(280px,0.9fr)]">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-4 w-4" />
                この unit で見るもの
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="mb-2 text-sm font-semibold">ターゲットスキル</div>
                <div className="rounded-md bg-muted/40 px-3 py-2 text-sm">
                  {session.target_skill}
                </div>
              </div>
              <KnowledgeList
                title="使ってよい知識"
                items={session.allowed_knowledge}
                tone="emerald"
              />
              <KnowledgeList
                title="今回は使わない知識"
                items={session.forbidden_knowledge}
                tone="amber"
              />
              <KnowledgeList
                title="前提 unit"
                items={
                  session.prerequisite_titles.length > 0
                    ? session.prerequisite_titles
                    : ["前提なし"]
                }
                tone="slate"
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>この 1 問のルール</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-muted-foreground">
              <p>新しい発想の持ち込みは不要です。</p>
              <p>提出後にのみ模範解答を表示します。</p>
              <p>
                {session.unit_kind === "integration"
                  ? "総合演習でも、既習 2 unit までの素直な組み合わせに限定します。"
                  : "この unit 単体の知識で解けるように絞っています。"}
              </p>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>{session.problem_title}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <MarkdownContent content={session.problem_statement} />

            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <h4 className="mb-1 font-semibold text-sm">入力形式</h4>
                <pre className="rounded bg-muted p-2 text-xs">
                  {session.input_format}
                </pre>
              </div>
              <div>
                <h4 className="mb-1 font-semibold text-sm">出力形式</h4>
                <pre className="rounded bg-muted p-2 text-xs">
                  {session.output_format}
                </pre>
              </div>
            </div>

            <div>
              <h4 className="mb-1 font-semibold text-sm">制約</h4>
              <pre className="rounded bg-muted p-2 text-xs">
                {session.constraints}
              </pre>
            </div>

            <div>
              <h4 className="mb-1 font-semibold text-sm">入出力例</h4>
              {session.examples.map((example, index) => (
                <div key={index} className="mb-2 grid gap-2 md:grid-cols-2">
                  <pre className="rounded bg-muted p-2 text-xs">
                    入力: {example.input}
                  </pre>
                  <pre className="rounded bg-muted p-2 text-xs">
                    出力: {example.output}
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
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={handleCodeKeyDown}
              placeholder="# Python で解答を書いてください"
              className="min-h-[320px] font-mono [tab-size:2]"
            />
            <Button
              onClick={handleSubmit}
              disabled={submitMutation.isPending || !draft.trim()}
              className="w-full"
            >
              {submitMutation.isPending ? "採点中..." : "提出"}
            </Button>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}

function KnowledgeList({
  title,
  items,
  tone,
}: {
  title: string;
  items: string[];
  tone: "emerald" | "amber" | "slate";
}) {
  const className = useMemo(() => {
    if (tone === "emerald") {
      return "border-emerald-400/25 bg-emerald-400/10 text-emerald-100";
    }
    if (tone === "amber") {
      return "border-amber-400/25 bg-amber-400/10 text-amber-100";
    }
    return "border-border bg-muted/40 text-foreground";
  }, [tone]);

  return (
    <div>
      <div className="mb-2 text-sm font-semibold">{title}</div>
      <div className="flex flex-wrap gap-2">
        {items.map((item) => (
          <span
            key={item}
            className={`rounded-full border px-2.5 py-1 text-xs ${className}`}
          >
            {item}
          </span>
        ))}
      </div>
    </div>
  );
}

function AlgorithmFoundationsResult({
  result,
  session,
  onBack,
}: {
  result: AlgorithmFoundationAnswerResponse;
  session: AlgorithmFoundationSessionResponse;
  onBack: () => void;
}) {
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
      <h1 className="text-2xl font-bold">結果: {session.unit_title}</h1>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-3">
            スコア
            <Badge
              variant={result.score >= 70 ? "default" : "destructive"}
              className="px-3 py-1 text-lg"
            >
              {result.score} / 100
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h4 className="mb-1 font-semibold">フィードバック</h4>
            <MarkdownContent content={result.feedback} />
          </div>

          {rubricScores.length > 0 && (
            <div>
              <h4 className="mb-2 font-semibold">採点内訳</h4>
              <div className="space-y-1">
                {rubricScores.map((score, index) => (
                  <div key={index} className="flex justify-between text-sm">
                    <span>{score.criterion}</span>
                    <span>
                      {score.points_awarded} / {score.points_max}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="grid gap-4 text-sm md:grid-cols-2">
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
            <h4 className="mb-1 font-semibold">改善提案</h4>
            <MarkdownContent content={result.improvement_suggestions} />
          </div>

          {result.reference_solution && (
            <div>
              <h4 className="mb-2 font-semibold">模範解答</h4>
              <pre className="overflow-x-auto rounded-md bg-[#0b1220] px-4 py-3.5 font-mono text-[13px] leading-relaxed text-[#e2e8f0]">
                {result.reference_solution}
              </pre>
            </div>
          )}
        </CardContent>
      </Card>

      <Button onClick={onBack} className="w-full">
        別の unit に進む
      </Button>
    </div>
  );
}
