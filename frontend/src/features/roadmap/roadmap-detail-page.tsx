import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Plus, TrendingUp, AlertTriangle, RotateCcw, ArrowLeft } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api";
import { useRoadmap } from "./use-roadmap";
import { useStartSession } from "./use-start-session";
import { useTreeStore } from "./use-tree-store";
import { RoadmapDetailHeader } from "./roadmap-detail-header";
import { RoadmapTree } from "./roadmap-tree";
import { TreeSkeleton } from "./tree-skeleton";
import { DetailEmptyState } from "./detail-empty-state";
import { ResumeSessionDialog } from "./resume-session-dialog";
import { AddItemDialog } from "./add-item-dialog";
import { DeleteConfirmDialog } from "./delete-confirm-dialog";
import { MoveItemDialog } from "./move-item-dialog";
import type { RoadmapTreeNode } from "@/types/api";

type DialogState =
  | { kind: null }
  | { kind: "resume"; node: RoadmapTreeNode; resumeSessionId: string }
  | { kind: "add"; parent: RoadmapTreeNode | null }
  | { kind: "delete"; node: RoadmapTreeNode }
  | { kind: "move"; node: RoadmapTreeNode };

type ErrorState = { message: string } | null;

function countDetails(nodes: RoadmapTreeNode[]): {
  total: number;
  attempted: number;
} {
  let total = 0;
  let attempted = 0;
  const walk = (arr: RoadmapTreeNode[]) => {
    for (const n of arr) {
      if (n.level === "detail") {
        total++;
        if (n.last_quiz_at) attempted++;
      }
      if (n.children?.length) walk(n.children);
    }
  };
  walk(nodes);
  return { total, attempted };
}

function countAllItems(nodes: RoadmapTreeNode[]): number {
  let n = 0;
  const walk = (arr: RoadmapTreeNode[]) => {
    for (const c of arr) {
      n++;
      walk(c.children ?? []);
    }
  };
  walk(nodes);
  return n;
}

export function RoadmapDetailPage() {
  const { roadmapId } = useParams<{ roadmapId: string }>();
  const navigate = useNavigate();
  const { data, isLoading, isError, error, refetch } = useRoadmap(
    roadmapId ?? "",
  );
  const startSession = useStartSession();
  const initExpanded = useTreeStore((s) => s.initExpanded);

  const [dlg, setDlg] = useState<DialogState>({ kind: null });
  const [dlgKey, setDlgKey] = useState(0);
  const [actionError, setActionError] = useState<ErrorState>(null);
  const closeDialog = useCallback(() => setDlg({ kind: null }), []);

  // Initialize tree expansion only once per roadmapId. The store tracks
  // which roadmapId it was initialized for, so re-navigating back preserves
  // the user's manually toggled expansion state.
  useEffect(() => {
    if (!data || !roadmapId) return;
    const majorIds = data.items
      .filter((n) => n.level === "major")
      .map((n) => n.id);
    initExpanded(roadmapId, majorIds);
  }, [data, roadmapId, initExpanded]);

  const openDlg = useCallback((state: DialogState) => {
    setDlgKey((k) => k + 1);
    setDlg(state);
  }, []);

  const handleStartQuiz = useCallback(
    async (node: RoadmapTreeNode) => {
      if (startSession.isPending) return;
      try {
        const result = await startSession.mutateAsync(node.id);
        if (result.resume_required && result.resume_session_id) {
          openDlg({
            kind: "resume",
            node,
            resumeSessionId: result.resume_session_id,
          });
        } else {
          navigate(`/sessions/${result.session_id}`, {
            state: { topic: data?.topic, roadmapId },
          });
        }
      } catch {
        setActionError({ message: "クイズの開始に失敗しました" });
      }
    },
    [startSession, navigate, openDlg, data?.topic, roadmapId],
  );

  const handleAddChild = useCallback(
    (parent: RoadmapTreeNode) => openDlg({ kind: "add", parent }),
    [openDlg],
  );

  const handleDelete = useCallback(
    (node: RoadmapTreeNode) => openDlg({ kind: "delete", node }),
    [openDlg],
  );

  const handleMove = useCallback(
    (node: RoadmapTreeNode) => openDlg({ kind: "move", node }),
    [openDlg],
  );

  const is404 =
    isError && error instanceof ApiError && error.status === 404;

  const crumbs = [
    { label: "ロードマップ", onClick: () => navigate("/roadmaps") },
    { label: data?.topic ?? "..." },
  ];

  const headerAction =
    !isLoading && !isError && data ? (
      <div className="flex gap-2">
        <Button variant="outline" disabled>
          <TrendingUp className="h-4 w-4" />
          統計
        </Button>
        <Button onClick={() => openDlg({ kind: "add", parent: null })}>
          <Plus className="h-4 w-4" />
          大枠を追加
        </Button>
      </div>
    ) : undefined;

  const details = data ? countDetails(data.items) : { total: 0, attempted: 0 };
  const itemTotal = data ? countAllItems(data.items) : 0;

  return (
    <>
      <AppShell crumbs={crumbs} action={headerAction}>
        {/* Loading */}
        {isLoading && (
          <>
            <div className="mb-7">
              <div className="h-8 w-1/3 animate-pulse rounded bg-muted" />
            </div>
            <TreeSkeleton />
          </>
        )}

        {/* Loaded */}
        {!isLoading && !isError && data && (
          <>
            <RoadmapDetailHeader
              topic={data.topic}
              overallScore={data.overall_score}
              detailAttempted={details.attempted}
              detailTotal={details.total}
              itemTotal={itemTotal}
            />
            {/* Action error banner */}
            {actionError && (
              <div className="mb-4 flex items-center justify-between rounded-md border border-rose-500/25 bg-rose-500/[0.08] px-4 py-2.5 text-sm text-rose-400">
                <span>{actionError.message}</span>
                <button
                  type="button"
                  className="cursor-pointer text-xs text-muted-foreground hover:text-foreground"
                  onClick={() => setActionError(null)}
                >
                  閉じる
                </button>
              </div>
            )}

            {data.items.length > 0 ? (
              <RoadmapTree
                items={data.items}
                detailCount={details.total}
                onStartQuiz={(n) => void handleStartQuiz(n)}
                onAddChild={handleAddChild}
                onDelete={handleDelete}
                onMove={handleMove}
                isStartingQuiz={startSession.isPending}
              />
            ) : (
              <DetailEmptyState
                onAdd={() => openDlg({ kind: "add", parent: null })}
              />
            )}
          </>
        )}

        {/* 404 */}
        {is404 && (
          <div className="mx-auto flex max-w-[480px] flex-col items-center px-6 pb-24 pt-14 text-center">
            <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-full border border-rose-500/25 bg-rose-500/10">
              <AlertTriangle className="h-9 w-9 text-rose-400" />
            </div>
            <div className="mb-1.5 text-base font-semibold tracking-tight">
              ロードマップが見つかりません
            </div>
            <div className="mb-6 text-[13px] leading-relaxed text-muted-foreground">
              削除されたか、URLが間違っている可能性があります
            </div>
            <Button onClick={() => navigate("/roadmaps")}>
              <ArrowLeft className="h-4 w-4" />
              ロードマップ一覧へ
            </Button>
          </div>
        )}

        {/* Generic error */}
        {isError && !is404 && (
          <div className="rounded-lg border border-border bg-card p-2">
            <div className="flex flex-col items-center px-6 pb-16 pt-14 text-center text-muted-foreground">
              <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full border border-rose-500/25 bg-rose-500/10">
                <AlertTriangle className="h-6 w-6 text-rose-400" />
              </div>
              <div className="mb-1 text-sm font-semibold text-foreground">
                読み込みに失敗しました
              </div>
              <div className="mb-5 max-w-[360px] text-xs leading-relaxed">
                ネットワークを確認してから、もう一度お試しください。
              </div>
              <Button onClick={() => void refetch()}>
                <RotateCcw className="h-4 w-4" />
                再読み込み
              </Button>
            </div>
          </div>
        )}
      </AppShell>

      {/* Dialogs */}
      <ResumeSessionDialog
        open={dlg.kind === "resume"}
        onOpenChange={(v) => {
          if (!v) closeDialog();
        }}
        node={dlg.kind === "resume" ? dlg.node : null}
        onResume={() => {
          if (dlg.kind === "resume") {
            closeDialog();
            navigate(`/sessions/${dlg.resumeSessionId}`, {
              state: { topic: data?.topic, roadmapId },
            });
          }
        }}
      />

      <AddItemDialog
        key={`add-${dlgKey}`}
        open={dlg.kind === "add"}
        onOpenChange={(v) => {
          if (!v) closeDialog();
        }}
        parent={dlg.kind === "add" ? dlg.parent : null}
        roadmapId={roadmapId ?? ""}
      />

      <DeleteConfirmDialog
        open={dlg.kind === "delete"}
        onOpenChange={(v) => {
          if (!v) closeDialog();
        }}
        node={dlg.kind === "delete" ? dlg.node : null}
        roadmapId={roadmapId ?? ""}
        onError={(msg) => setActionError({ message: msg })}
      />

      <MoveItemDialog
        key={`move-${dlgKey}`}
        open={dlg.kind === "move"}
        onOpenChange={(v) => {
          if (!v) closeDialog();
        }}
        node={dlg.kind === "move" ? dlg.node : null}
        tree={data?.items ?? []}
        roadmapId={roadmapId ?? ""}
        onError={(msg) => setActionError({ message: msg })}
      />
    </>
  );
}
