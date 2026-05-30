import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Play } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { GeneratingDialog } from "@/components/common/generating-dialog";
import { useThemes, useStartSession } from "./use-competitive";
import { useCompetitiveStore } from "./use-competitive-store";

const PHASES = [
  { label: "基礎", min: 0, max: 19 },
  { label: "基本", min: 20, max: 39 },
  { label: "中級", min: 40, max: 69 },
  { label: "上級", min: 70, max: 99 },
  { label: "発展", min: 100, max: 130 },
] as const;

export function CompetitivePage() {
  const { data, isLoading, isError } = useThemes();
  const startMutation = useStartSession();
  const { setSession } = useCompetitiveStore();
  const navigate = useNavigate();
  const [generatingTarget, setGeneratingTarget] = useState("");

  const { phaseGroups, nextThemeId, nextThemeLabel } = useMemo(() => {
    if (!data?.themes) return { phaseGroups: [], nextThemeId: null as string | null, nextThemeLabel: null as string | null };
    const groups = PHASES.map((phase) => ({
      label: phase.label,
      themes: data.themes.filter(
        (t) => t.display_order >= phase.min && t.display_order <= phase.max,
      ),
    }));
    const next = data.themes.find((t) => t.attempt_count === 0);
    return { phaseGroups: groups, nextThemeId: next?.id ?? null, nextThemeLabel: next?.label ?? null };
  }, [data]);

  const handleStart = async (themeId?: string, label?: string) => {
    setGeneratingTarget(label ?? nextThemeLabel ?? "");
    try {
      const result = await startMutation.mutateAsync(themeId);
      setSession(result);
      navigate(`/algorithm-quiz/${result.session_id}`);
    } catch {
      // TanStack Query handles error state
    }
  };

  return (
    <AppShell crumbs={[{ label: "競プロクイズ" }]}>
      <GeneratingDialog
        open={startMutation.isPending}
        target={generatingTarget}
        description="テーマに沿った問題を出題します"
      />

      {isError && (
        <div className="rounded-md bg-destructive/10 p-4 text-destructive">
          テーマの読み込みに失敗しました。
        </div>
      )}

      {startMutation.isError && (
        <div className="rounded-md bg-destructive/10 p-4 text-destructive">
          セッションの開始に失敗しました。
        </div>
      )}

      {isLoading ? (
        <div className="animate-pulse space-y-4">
          <div className="h-8 w-48 rounded bg-muted" />
          <div className="h-64 rounded bg-muted" />
        </div>
      ) : (
        <div className="space-y-6">
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold">競プロクイズ</h1>
            <Button
              size="sm"
              onClick={() => handleStart()}
              disabled={startMutation.isPending}
            >
              <Play className="mr-1.5 h-3.5 w-3.5" />
              {nextThemeLabel ? `次: ${nextThemeLabel}` : "挑戦する"}
            </Button>
          </div>

          <div className="space-y-4">
            {phaseGroups.map((group) => (
              <Card key={group.label}>
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg">{group.label}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {group.themes.map((theme) => (
                      <Badge
                        key={theme.id}
                        variant={theme.attempt_count > 0 ? "secondary" : "outline"}
                        className={[
                          "py-1.5 px-3 text-sm",
                          startMutation.isPending
                            ? "opacity-50"
                            : "cursor-pointer hover:bg-accent",
                          theme.id === nextThemeId
                            ? "ring-2 ring-primary ring-offset-1 ring-offset-background"
                            : "",
                        ].join(" ")}
                        onClick={() =>
                          !startMutation.isPending && handleStart(theme.id, theme.label)
                        }
                      >
                        <span className="mr-1.5 text-[11px] text-muted-foreground">
                          {theme.category}
                        </span>
                        {theme.label}
                        {theme.best_score != null && (
                          <span className={`ml-2 text-[11px] font-semibold ${theme.best_score >= 70 ? "text-emerald-400" : "text-orange-400"}`}>
                            {theme.best_score}
                          </span>
                        )}
                      </Badge>
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
