import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Database, Play } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { GeneratingDialog } from "@/components/common/generating-dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  useSqlDojoCatalog,
  useStartSqlDojoSession,
} from "./use-sql-dojo";
import { useSqlDojoStore } from "./use-sql-dojo-store";
import type { SqlDojoDifficulty, SqlDojoThemeSummary } from "@/types/api";

const DIFFICULTY_LABELS: Record<SqlDojoDifficulty, string> = {
  beginner: "初級",
  intermediate: "中級",
  advanced: "上級",
};

const STORAGE_KEY = "sql-dojo-difficulty";

export function SqlDojoPage() {
  const navigate = useNavigate();
  const { data, isLoading, isError } = useSqlDojoCatalog();
  const startMutation = useStartSqlDojoSession();
  const { setSession } = useSqlDojoStore();
  const [difficulty, setDifficulty] = useState<SqlDojoDifficulty>(() => {
    const saved = window.localStorage.getItem(STORAGE_KEY);
    if (
      saved === "beginner" ||
      saved === "intermediate" ||
      saved === "advanced"
    ) {
      return saved;
    }
    return "beginner";
  });
  const [generatingTarget, setGeneratingTarget] = useState("");

  const themesByDifficulty = useMemo(() => {
    const groups: Record<SqlDojoDifficulty, SqlDojoThemeSummary[]> = {
      beginner: [],
      intermediate: [],
      advanced: [],
    };
    for (const theme of data?.themes ?? []) {
      groups[theme.difficulty].push(theme);
    }
    return groups;
  }, [data]);

  const selectedThemes = themesByDifficulty[difficulty] ?? [];

  const start = async (themeFamily?: string, themeTitle?: string) => {
    setGeneratingTarget(themeTitle ?? DIFFICULTY_LABELS[difficulty]);
    try {
      const result = await startMutation.mutateAsync({
        difficulty,
        themeFamily,
      });
      setSession(result);
      window.localStorage.setItem(STORAGE_KEY, difficulty);
      navigate(`/sql-dojo/${result.session_id}`);
    } catch {
      // handled by query state
    }
  };

  return (
    <AppShell crumbs={[{ label: "SQL道場" }]}>
      <GeneratingDialog
        open={startMutation.isPending}
        target={generatingTarget}
        description="1問だけ解いて、継続しやすいペースで SQL を鍛えます"
      />

      {isError && (
        <div className="rounded-md bg-destructive/10 p-4 text-destructive">
          SQL道場カタログの読み込みに失敗しました。
        </div>
      )}

      {startMutation.isError && (
        <div className="rounded-md bg-destructive/10 p-4 text-destructive">
          SQL道場セッションの開始に失敗しました。
        </div>
      )}

      {isLoading ? (
        <div className="animate-pulse space-y-4">
          <div className="h-8 w-56 rounded bg-muted" />
          <div className="h-64 rounded bg-muted" />
        </div>
      ) : (
        <div className="space-y-6">
          <div className="flex flex-wrap items-end gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Database className="h-5 w-5 text-cyan-400" />
                <h1 className="text-2xl font-bold">SQL道場</h1>
              </div>
              <p className="text-sm text-muted-foreground">
                1セッション1問で、実務寄りの SQL を継続的に鍛えます
              </p>
            </div>

            <div className="ml-auto flex items-center gap-3">
              <label className="text-sm text-muted-foreground" htmlFor="sql-dojo-difficulty">
                難易度
              </label>
              <select
                id="sql-dojo-difficulty"
                className="rounded-md border border-border bg-card px-3 py-2 text-sm"
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value as SqlDojoDifficulty)}
              >
                {data?.difficulties.map((item) => (
                  <option key={item} value={item}>
                    {DIFFICULTY_LABELS[item]}
                  </option>
                ))}
              </select>
              <Button
                size="sm"
                onClick={() => start()}
                disabled={startMutation.isPending}
              >
                <Play className="mr-1.5 h-3.5 w-3.5" />
                次の1問
              </Button>
            </div>
          </div>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">
                {DIFFICULTY_LABELS[difficulty]}のテーマ
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {selectedThemes.length === 0 ? (
                <div className="text-sm text-muted-foreground">
                  この難易度のテーマはまだありません。
                </div>
              ) : (
                selectedThemes.map((theme) => (
                  <button
                    key={`${theme.family}-${theme.title}`}
                    type="button"
                    className="flex w-full items-start justify-between rounded-lg border border-border bg-card px-4 py-3 text-left transition-colors hover:bg-accent"
                    onClick={() => start(theme.family, theme.title)}
                    disabled={startMutation.isPending}
                  >
                    <div className="space-y-1">
                      <div className="font-medium">{theme.title}</div>
                      <div className="text-sm text-muted-foreground">
                        {theme.business_domain} / {theme.target_skill}
                      </div>
                    </div>
                    <Badge variant="outline">{theme.family}</Badge>
                  </button>
                ))
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </AppShell>
  );
}
