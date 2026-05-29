import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Map,
  TrendingUp,
  MessageSquare,
  BookOpenText,
  AlertTriangle,
  X,
  Swords,
} from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { scoreLevel } from "@/lib/score";
import { useDashboardData } from "./use-dashboard-data";
import { StatCard } from "./stat-card";
import {
  StatSkeleton,
  RoadmapSectionSkeleton,
  ActivitySectionSkeleton,
} from "./dashboard-skeleton";
import { RoadmapSummary } from "./roadmap-summary";
import { RecentActivity } from "./recent-activity";
import { DashboardWelcome } from "./dashboard-welcome";

export function DashboardPage() {
  const navigate = useNavigate();
  const {
    stats,
    competitiveStats,
    roadmaps,
    totalRoadmapCount,
    activity,
    isLoading,
    isError,
    isEmpty,
    refetch,
  } = useDashboardData();

  // Error toast
  const [showErrorToast, setShowErrorToast] = useState(false);
  useEffect(() => {
    if (isError) setShowErrorToast(true);
  }, [isError]);

  const crumbs = [{ label: "ダッシュボード" }];
  const hasAvgScore = stats?.avgScore != null && stats.avgScore > 0;
  const avgLvl = hasAvgScore ? scoreLevel(stats.avgScore) : null;

  // State conditions — use isLoading as primary gating
  const showSkeleton = isLoading;
  const showLoaded = !isLoading && stats != null && !isEmpty;
  const showEmpty = !isLoading && isEmpty;

  // Stat card rendering — shared between loaded and empty states
  const statCards = stats && (
    <div className="grid grid-cols-5 gap-4 max-[1180px]:grid-cols-2">
      <StatCard
        icon={Map}
        label="学習中のロードマップ"
        value={stats.roadmapCount}
      />
      <StatCard
        icon={TrendingUp}
        label="全体の平均スコア"
        value={hasAvgScore ? stats.avgScore! : "—"}
        valueColor={avgLvl?.fg}
        hint={avgLvl ? avgLvl.label : "未計測"}
      />
      <StatCard
        icon={MessageSquare}
        label="未読フィードバック"
        value={stats.unreadCount}
        onClick={() => navigate("/feedbacks")}
        hot={stats.unreadCount > 0}
        hint={stats.unreadCount > 0 ? "クリックして一覧へ" : "すべて既読"}
      />
      <StatCard
        icon={BookOpenText}
        label="直近7日間のクイズ"
        value={stats.recentQuizCount}
        suffix=" 回"
        hint={
          stats.recentQuizCount >= 5 ? "安定したペース" : "もう少し増やせます"
        }
      />
      <StatCard
        icon={Swords}
        label="競プロクイズ"
        value={competitiveStats.totalCount ?? "—"}
        onClick={() => navigate("/algorithm-quiz")}
        hint={
          competitiveStats.totalCount == null
            ? "読み込み中"
            : competitiveStats.avgScore != null
              ? `平均 ${competitiveStats.avgScore} 点`
              : "未挑戦"
        }
      />
    </div>
  );

  return (
    <>
      <AppShell crumbs={crumbs}>
        {/* Page header */}
        <div className="mb-6">
          <h1 className="text-xl font-semibold tracking-tight">
            ダッシュボード
          </h1>
          <p className="mt-1.5 text-sm text-muted-foreground">
            {showSkeleton && "読み込み中…"}
            {showEmpty && "まだロードマップがありません"}
            {showLoaded && "学習の全体像と次にやることをここで決めます"}
            {!showSkeleton && !stats && isError && "読み込みエラー"}
          </p>
        </div>

        {/* Loading skeleton */}
        {showSkeleton && (
          <>
            <div className="grid grid-cols-5 gap-4 max-[1180px]:grid-cols-2">
              {[0, 1, 2, 3, 4].map((i) => (
                <StatSkeleton key={i} />
              ))}
            </div>
            <div className="mt-6 grid grid-cols-[minmax(0,1fr)_minmax(0,1.05fr)] gap-4 max-[980px]:grid-cols-1">
              <RoadmapSectionSkeleton rows={5} />
              <ActivitySectionSkeleton rows={6} />
            </div>
          </>
        )}

        {/* Loaded state — stat cards + two-column block */}
        {showLoaded && (
          <>
            {statCards}
            <div className="mt-6 grid grid-cols-[minmax(0,1fr)_minmax(0,1.05fr)] gap-4 max-[980px]:grid-cols-1">
              <RoadmapSummary
                roadmaps={roadmaps}
                totalCount={totalRoadmapCount}
              />
              <RecentActivity activity={activity} />
            </div>
          </>
        )}

        {/* Empty state — stat cards (all 0/—) + welcome */}
        {showEmpty && (
          <>
            {statCards}
            <DashboardWelcome />
          </>
        )}
      </AppShell>

      {/* Error toast — retry does not close toast; toast persists until
          user explicitly dismisses or the next successful load */}
      {showErrorToast && (
        <div
          role="alert"
          className="fixed bottom-6 left-1/2 z-40 flex min-w-[320px] -translate-x-1/2 animate-[toast-in_200ms_ease-out] items-center gap-3 rounded-lg border border-[rgb(244_63_94/0.4)] border-l-[3px] border-l-[#fb7185] bg-card px-4 py-3 text-[13px] text-foreground shadow-[0_12px_32px_-8px_rgb(0_0_0/0.6)]"
        >
          <AlertTriangle className="h-4 w-4 shrink-0 text-[#fb7185]" />
          <div className="flex-1">
            <div className="font-medium">
              ダッシュボードの取得に失敗しました
            </div>
            <div className="mt-0.5 text-xs text-muted-foreground">
              ネットワーク接続を確認するか、少し待ってからもう一度お試しください
            </div>
          </div>
          <button
            type="button"
            className="inline-flex cursor-pointer items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
            onClick={() => void refetch()}
          >
            再読み込み
          </button>
          <button
            type="button"
            className="inline-flex cursor-pointer items-center p-1 text-muted-foreground hover:text-foreground"
            onClick={() => setShowErrorToast(false)}
            aria-label="閉じる"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      )}
    </>
  );
}
