import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AlertTriangle, Play, Target } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { GeneratingDialog } from "@/components/common/generating-dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import {
  useAlgorithmFoundationsCatalog,
  useAlgorithmFoundationSessions,
  useStartAlgorithmFoundationSession,
} from "./use-algorithm-foundations";
import type {
  AlgorithmFoundationGroupSummary,
  AlgorithmFoundationSessionListItem,
  AlgorithmFoundationUnitKind,
  AlgorithmFoundationUnitSummary,
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

function groupAnchorId(groupId: string) {
  return `foundation-group-${groupId}`;
}

function unstartedCount(group: AlgorithmFoundationGroupSummary) {
  return group.units.filter((unit) => unit.best_score == null).length;
}

function prerequisiteSummary(unit: AlgorithmFoundationUnitSummary) {
  if (unit.prerequisite_titles.length === 0) return "前提なし";
  const visible = unit.prerequisite_titles.slice(0, 2).join(" / ");
  if (unit.prerequisite_titles.length <= 2) {
    return `前提: ${visible}`;
  }
  return `前提 ${unit.prerequisite_titles.length} 件: ${visible} / ほか${unit.prerequisite_titles.length - 2}件`;
}

export function AlgorithmFoundationsPage() {
  const navigate = useNavigate();
  const catalogQuery = useAlgorithmFoundationsCatalog();
  const sessionsQuery = useAlgorithmFoundationSessions();
  const startMutation = useStartAlgorithmFoundationSession();
  const [generatingTarget, setGeneratingTarget] = useState("");

  const recommendedUnit = useMemo(() => {
    for (const group of catalogQuery.data?.groups ?? []) {
      const match = group.units.find((unit) => unit.recommended);
      if (match) return match;
    }
    return null;
  }, [catalogQuery.data]);

  const recentSessions = useMemo(
    () => (sessionsQuery.data?.sessions ?? []).slice(0, 6),
    [sessionsQuery.data],
  );

  const start = async (unit?: AlgorithmFoundationUnitSummary) => {
    setGeneratingTarget(unit?.title ?? recommendedUnit?.title ?? "次の1問");
    try {
      const result = await startMutation.mutateAsync(unit?.unit_id);
      navigate(`/algorithm-foundations/${result.session_id}`);
    } catch {
      // handled by query state
    }
  };

  return (
    <AppShell crumbs={[{ label: "競プロうさぎ" }]}>
      <GeneratingDialog
        open={startMutation.isPending}
        target={generatingTarget}
        description="前提を絞った 1 問を開始します"
      />

      {catalogQuery.isError && (
        <div className="rounded-md bg-destructive/10 p-4 text-destructive">
          競プロうさぎカタログの読み込みに失敗しました。
        </div>
      )}

      {startMutation.isError && (
        <div className="rounded-md bg-destructive/10 p-4 text-destructive">
          セッションの開始に失敗しました。
        </div>
      )}

      {catalogQuery.isLoading ? (
        <div className="animate-pulse space-y-4">
          <div className="h-8 w-56 rounded bg-muted" />
          <div className="h-64 rounded bg-muted" />
        </div>
      ) : (
        <div className="space-y-6">
          <div className="flex flex-wrap items-end gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Target className="h-5 w-5 text-emerald-300" />
                <h1 className="text-2xl font-bold">競プロうさぎ</h1>
              </div>
              <p className="text-sm text-muted-foreground">
                講義なし、1セッション1問、前提知識を絞った基礎 unit を順番に積みます
              </p>
              <p className="text-sm text-muted-foreground">
                全 {catalogQuery.data?.total_unit_count ?? 0} unit / {catalogQuery.data?.total_problem_count ?? 0} 問
              </p>
            </div>

            <div className="ml-auto flex flex-wrap items-center gap-3">
              <div className="rounded-md border border-border bg-card px-3 py-2 text-sm text-muted-foreground">
                前提未達でも開始できます。ロックはしません。
              </div>
              <Button
                size="sm"
                onClick={() => start(recommendedUnit ?? undefined)}
                disabled={startMutation.isPending || recommendedUnit == null}
              >
                <Play className="mr-1.5 h-3.5 w-3.5" />
                {recommendedUnit ? `次: ${recommendedUnit.title}` : "次の1問"}
              </Button>
            </div>
          </div>

          {recentSessions.length > 0 && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">最近の挑戦</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                  {recentSessions.map((session) => (
                    <RecentSessionCard
                      key={session.session_id}
                      session={session}
                      onOpen={() =>
                        navigate(`/algorithm-foundations/${session.session_id}`)
                      }
                    />
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {(catalogQuery.data?.groups.length ?? 0) > 0 && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">目次</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
                  {catalogQuery.data?.groups.map((group) => (
                    <a
                      key={group.group_id}
                      href={`#${groupAnchorId(group.group_id)}`}
                      className="rounded-md border border-border bg-card px-3 py-2 text-sm transition-colors hover:bg-[rgb(51_65_85/0.25)]"
                    >
                      <div className="font-medium">{group.group_title}</div>
                      <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                        <span>{group.units.length} unit</span>
                        <span>未着手 {unstartedCount(group)}</span>
                      </div>
                    </a>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          <div className="space-y-4">
            {catalogQuery.data?.groups.map((group) => (
              <Card key={group.group_id} id={groupAnchorId(group.group_id)}>
                <CardHeader className="pb-3">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <CardTitle className="text-lg">
                      {group.group_title}
                      <span className="ml-2 text-sm font-normal text-muted-foreground">
                        {group.units.length} unit
                      </span>
                    </CardTitle>
                    <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                      <span>未着手 {unstartedCount(group)}</span>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-3">
                    {group.units.map((unit) => (
                      <UnitCard
                        key={unit.unit_id}
                        unit={unit}
                        onStart={() => start(unit)}
                        disabled={startMutation.isPending}
                      />
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </AppShell>
  );
}

function UnitCard({
  unit,
  onStart,
  disabled,
}: {
  unit: AlgorithmFoundationUnitSummary;
  onStart: () => void;
  disabled: boolean;
}) {
  const prerequisiteLabel = prerequisiteSummary(unit);

  return (
    <div
      className={cn(
        "rounded-lg border border-border bg-card px-3 py-3",
        unit.recommended && "ring-1 ring-emerald-400/70",
      )}
    >
      <div className="flex items-start gap-3">
        <div className="min-w-0 flex-1 space-y-2">
          <div className="flex flex-wrap items-center gap-1.5">
            <div className="truncate text-sm font-medium">{unit.title}</div>
            <Badge
              variant={unit.unit_kind === "integration" ? "outline" : "secondary"}
            >
              {unitKindLabel(unit.unit_kind)}
            </Badge>
            {unit.recommended && <Badge>推奨</Badge>}
            {unit.has_unmet_prerequisites && (
              <Badge
                variant="outline"
                className="border-amber-400/40 text-amber-100"
              >
                <AlertTriangle className="mr-1 h-3 w-3" />
                前提注意
              </Badge>
            )}
          </div>

          {unit.target_skill !== unit.title && (
            <div className="text-xs text-muted-foreground">{unit.target_skill}</div>
          )}

          <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-[11px] text-muted-foreground">
            <span>{unit.problem_count} 問</span>
            <span className={scoreTone(unit.best_score)}>
              {unit.best_score != null ? `最高 ${unit.best_score} 点` : "未着手"}
            </span>
            <span>{prerequisiteLabel}</span>
          </div>
        </div>

        <Button
          size="sm"
          variant={unit.recommended ? "default" : "secondary"}
          onClick={onStart}
          disabled={disabled}
          className="h-8 shrink-0 px-3"
        >
          解く
        </Button>
      </div>
    </div>
  );
}

function RecentSessionCard({
  session,
  onOpen,
}: {
  session: AlgorithmFoundationSessionListItem;
  onOpen: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onOpen}
      className="space-y-2 rounded-lg border border-border bg-card px-4 py-3 text-left transition-colors hover:bg-[rgb(51_65_85/0.25)]"
    >
      <div className="flex items-center justify-between gap-3">
        <div className="truncate font-medium">{session.unit_title}</div>
        <Badge variant={session.status === "completed" ? "secondary" : "outline"}>
          {session.status === "completed" ? "完了" : "途中"}
        </Badge>
      </div>
      <div className="text-sm text-muted-foreground">{session.target_skill}</div>
      <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
        <span>{session.group_title}</span>
        <span>・</span>
        <span>{unitKindLabel(session.unit_kind)}</span>
        {session.score != null && (
          <>
            <span>・</span>
            <span className={scoreTone(session.score)}>最高 {session.score} 点</span>
          </>
        )}
      </div>
    </button>
  );
}
