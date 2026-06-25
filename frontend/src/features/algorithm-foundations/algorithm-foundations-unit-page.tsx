import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { AlertTriangle, ListChecks, Target } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { GeneratingDialog } from "@/components/common/generating-dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  PROGRAMMING_LANGUAGE_STORAGE_KEY,
} from "@/lib/programming-language";
import {
  useAlgorithmFoundationLanguages,
  useAlgorithmFoundationUnit,
  useStartAlgorithmFoundationSession,
} from "./use-algorithm-foundations";
import type {
  AlgorithmFoundationUnitKind,
  CompetitiveLanguageOption,
} from "@/types/api";

function unitKindLabel(kind: AlgorithmFoundationUnitKind) {
  return kind === "integration" ? "総合演習" : "基礎";
}

function scoreTone(score: number | null) {
  if (score == null) return "text-muted-foreground";
  if (score >= 80) return "text-emerald-400";
  if (score >= 60) return "text-amber-300";
  return "text-orange-400";
}

export function AlgorithmFoundationsUnitPage() {
  const { unitId } = useParams<{ unitId: string }>();
  const navigate = useNavigate();

  if (!unitId) {
    navigate("/algorithm-foundations");
    return null;
  }

  return <AlgorithmFoundationsUnitPageInner key={unitId} unitId={unitId} />;
}

function AlgorithmFoundationsUnitPageInner({ unitId }: { unitId: string }) {
  const navigate = useNavigate();
  const languagesQuery = useAlgorithmFoundationLanguages();
  const unitQuery = useAlgorithmFoundationUnit(unitId);
  const startMutation = useStartAlgorithmFoundationSession();
  const [generatingTarget, setGeneratingTarget] = useState("");
  const [programmingLanguage, setProgrammingLanguage] = useState(
    () =>
      window.localStorage.getItem(PROGRAMMING_LANGUAGE_STORAGE_KEY) ?? "python",
  );

  const unit = unitQuery.data;
  const languages = languagesQuery.data?.languages ?? [];
  const selectedLanguage =
    languages.find((item) => item.id === programmingLanguage) ?? null;
  const resolvedLanguage = selectedLanguage ?? languages[0] ?? null;
  const selectValue = resolvedLanguage?.id ?? programmingLanguage;

  useEffect(() => {
    if (resolvedLanguage && resolvedLanguage.id !== programmingLanguage) {
      window.localStorage.setItem(
        PROGRAMMING_LANGUAGE_STORAGE_KEY,
        resolvedLanguage.id,
      );
    }
  }, [programmingLanguage, resolvedLanguage]);

  const startProblem = async (problemId: string, title: string) => {
    if (!resolvedLanguage) {
      return;
    }
    setGeneratingTarget(title);
    try {
      const result = await startMutation.mutateAsync({
        unitId,
        problemId,
        programmingLanguage: resolvedLanguage.id,
      });
      navigate(`/algorithm-foundations/${result.session_id}`);
    } catch {
      // handled by query state
    }
  };

  if (unitQuery.isLoading) {
    return (
      <AppShell crumbs={[{ label: "競プロうさぎ" }, { label: "読み込み中..." }]}>
        <div className="animate-pulse space-y-4">
          <div className="h-8 w-56 rounded bg-muted" />
          <div className="h-72 rounded bg-muted" />
        </div>
      </AppShell>
    );
  }

  if (unitQuery.isError || !unit) {
    return (
      <AppShell crumbs={[{ label: "競プロうさぎ" }, { label: "エラー" }]}>
        <div className="rounded-md bg-destructive/10 p-4 text-destructive">
          unit の読み込みに失敗しました。
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

  return (
    <AppShell
      crumbs={[
        { label: "競プロうさぎ", onClick: () => navigate("/algorithm-foundations") },
        { label: unit.title },
      ]}
    >
      <GeneratingDialog
        open={startMutation.isPending}
        target={generatingTarget}
        description="選んだ問題を開始します"
      />

      <div className="space-y-6">
        {languagesQuery.isError && (
          <div className="rounded-md bg-destructive/10 p-4 text-destructive">
            出題言語の取得に失敗しました。
          </div>
        )}

        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <Target className="h-5 w-5 text-emerald-300" />
              <h1 className="text-2xl font-bold">{unit.title}</h1>
              <Badge variant="outline">{unit.group_title}</Badge>
              <Badge variant="secondary">{unitKindLabel(unit.unit_kind)}</Badge>
            </div>
            <p className="max-w-3xl text-sm leading-6 text-muted-foreground">
              {unit.concept_overview}
            </p>
            <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
              <span>{unit.problem_count} 問</span>
              <span className={scoreTone(unit.best_score)}>
                {unit.best_score != null ? `最高 ${unit.best_score} 点` : "未着手"}
              </span>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <select
              aria-label="出題言語"
              className="rounded-md border border-border bg-card px-3 py-2 text-sm"
              value={selectValue}
              onChange={(e) => {
                setProgrammingLanguage(e.target.value);
                window.localStorage.setItem(
                  PROGRAMMING_LANGUAGE_STORAGE_KEY,
                  e.target.value,
                );
              }}
              disabled={languagesQuery.isLoading || languagesQuery.isError}
            >
              {languages.map((language: CompetitiveLanguageOption) => (
                <option key={language.id} value={language.id}>
                  {language.label}
                </option>
              ))}
            </select>
            <Button
              variant="secondary"
              onClick={() => navigate("/algorithm-foundations")}
            >
              一覧に戻る
            </Button>
          </div>
        </div>

        {unit.has_unmet_prerequisites && (
          <div className="flex items-start gap-2 rounded-md border border-amber-400/30 bg-amber-400/10 p-4 text-amber-100">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            <div className="space-y-1 text-sm">
              <div className="font-medium">前提未達の unit があります</div>
              <div>{unit.prerequisite_titles.join(" / ")} を先に触れると理解しやすくなります。</div>
            </div>
          </div>
        )}

        {startMutation.isError && (
          <div className="rounded-md bg-destructive/10 p-4 text-destructive">
            セッションの開始に失敗しました。
          </div>
        )}

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ListChecks className="h-4 w-4" />
              問題一覧
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {unit.problems.map((problem) => (
              <div
                key={problem.problem_id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border bg-card px-3 py-3"
              >
                <div className="space-y-1">
                  <div className="font-medium">{problem.title}</div>
                  <div className="text-xs text-muted-foreground">
                    <span className={scoreTone(problem.best_score)}>
                      {problem.best_score != null ? `最高 ${problem.best_score} 点` : "-"}
                    </span>
                  </div>
                </div>
                <Button
                  size="sm"
                  onClick={() => startProblem(problem.problem_id, problem.title)}
                  disabled={
                    startMutation.isPending ||
                    languagesQuery.isLoading ||
                    languagesQuery.isError ||
                    resolvedLanguage == null
                  }
                >
                  この問題を解く
                </Button>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
