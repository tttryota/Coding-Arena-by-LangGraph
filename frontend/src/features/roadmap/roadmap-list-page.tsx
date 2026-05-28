import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, AlertTriangle, RotateCcw } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { useRoadmaps } from "./use-roadmaps";
import { RoadmapCard } from "./roadmap-card";
import { SkeletonCard } from "./skeleton-card";
import { EmptyState } from "./empty-state";
import { GenerateRoadmapDialog } from "./generate-dialog";

export function RoadmapListPage() {
  const navigate = useNavigate();
  const { data, isLoading, isError, refetch } = useRoadmaps();
  const roadmaps = data?.items ?? [];
  const hasRoadmaps = roadmaps.length > 0;
  const isLoaded = !isLoading && !isError;
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogKey, setDialogKey] = useState(0);

  const openDialog = useCallback(() => {
    setDialogKey((k) => k + 1);
    setDialogOpen(true);
  }, []);
  const closeDialog = useCallback(() => setDialogOpen(false), []);
  const handleSuccess = useCallback(
    (roadmapId: string) => {
      closeDialog();
      navigate(`/roadmaps/${roadmapId}`);
    },
    [closeDialog, navigate],
  );

  const showCreateButton = isLoaded && hasRoadmaps;
  const summaryText = isLoading
    ? "読み込み中…"
    : isError
      ? "読み込みエラー"
      : hasRoadmaps
        ? `${roadmaps.length} 件のロードマップ・作成順`
        : "学習を始めるには、まずロードマップを作成してください";

  return (
    <>
      <AppShell
        crumbs={[{ label: "ロードマップ" }]}
        action={
          showCreateButton ? (
            <Button onClick={openDialog}>
              <Plus className="h-4 w-4" />
              新規作成
            </Button>
          ) : undefined
        }
      >
        {/* Page header */}
        <div className="mb-6">
          <h1 className="text-xl font-semibold tracking-tight">ロードマップ</h1>
          <p className="mt-1.5 text-sm text-muted-foreground">{summaryText}</p>
        </div>

        {/* Card grid */}
        {isLoaded && hasRoadmaps && (
          <div className="grid grid-cols-3 gap-4 max-[1180px]:grid-cols-2">
            {roadmaps.map((r) => (
              <RoadmapCard
                key={r.roadmap_id}
                roadmap={r}
                onClick={() => navigate(`/roadmaps/${r.roadmap_id}`)}
              />
            ))}
          </div>
        )}

        {/* Skeleton loading */}
        {isLoading && (
          <div className="grid grid-cols-3 gap-4 max-[1180px]:grid-cols-2">
            {Array.from({ length: 6 }, (_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        )}

        {/* Empty state */}
        {isLoaded && !hasRoadmaps && <EmptyState onCreate={openDialog} />}

        {/* Error state */}
        {isError && (
          <div className="mx-auto flex max-w-[480px] flex-col items-center px-6 pb-24 pt-[72px] text-center">
            <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-full border border-rose-500/25 bg-rose-500/10">
              <AlertTriangle className="h-9 w-9 text-rose-400" />
            </div>
            <div className="mb-1.5 text-base font-semibold tracking-tight">
              ロードマップの読み込みに失敗しました
            </div>
            <div className="mb-6 text-[13px] leading-relaxed text-muted-foreground">
              ネットワーク接続を確認するか、少し待ってからもう一度お試しください
            </div>
            <Button onClick={() => void refetch()}>
              <RotateCcw className="h-4 w-4" />
              再読み込み
            </Button>
          </div>
        )}
      </AppShell>

      <GenerateRoadmapDialog
        key={dialogKey}
        open={dialogOpen}
        onClose={closeDialog}
        onSuccess={handleSuccess}
      />
    </>
  );
}
