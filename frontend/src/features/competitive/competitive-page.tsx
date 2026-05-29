import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Shuffle } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { useThemes, useStartSession } from "./use-competitive";
import { useCompetitiveStore } from "./use-competitive-store";

export function CompetitivePage() {
  const { data, isLoading, isError } = useThemes();
  const startMutation = useStartSession();
  const { setSession } = useCompetitiveStore();
  const navigate = useNavigate();

  const grouped = useMemo(() => {
    if (!data?.themes) return new Map<string, typeof data.themes>();
    const map = new Map<string, typeof data.themes>();
    for (const theme of data.themes) {
      const list = map.get(theme.category) ?? [];
      list.push(theme);
      map.set(theme.category, list);
    }
    return map;
  }, [data]);

  const handleStart = async (themeId?: string) => {
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
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold">競プロクイズ</h1>
            <Button
              onClick={() => handleStart()}
              disabled={startMutation.isPending}
            >
              <Shuffle className="mr-2 h-4 w-4" />
              ランダムで挑戦
            </Button>
          </div>

          <div className="space-y-4">
            {[...grouped.entries()].map(([category, themes]) => (
              <Card key={category}>
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg">{category}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {themes.map((theme) => (
                      <Badge
                        key={theme.id}
                        variant="outline"
                        className="cursor-pointer hover:bg-accent"
                        onClick={() => handleStart(theme.id)}
                      >
                        {theme.label}
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
