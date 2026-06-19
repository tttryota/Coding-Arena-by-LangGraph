import { useMemo, useCallback } from "react";
import { useQuery, useQueries } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { useRoadmaps } from "@/features/roadmap/use-roadmaps";
import { useCompetitiveSessions } from "@/features/competitive/use-competitive";
import { useSqlDojoSessions } from "@/features/sql-dojo/use-sql-dojo";
import type {
  RoadmapListItem,
  RoadmapTree,
  RoadmapTreeNode,
  FeedbackListItem,
  FeedbackListResponse,
  SqlDojoSessionListItem,
} from "@/types/api";

// ---------------------------------------------------------------------------
// Public types
// ---------------------------------------------------------------------------

export interface DashboardStats {
  roadmapCount: number;
  avgScore: number | null;
  unreadCount: number;
  recentQuizCount: number;
}

export interface QuizActivity {
  kind: "quiz";
  itemId: string;
  title: string;
  score: number;
  roadmapId: string;
  lastQuizAt: string;
}

export interface FeedbackActivity {
  kind: "feedback";
  id: string;
  title: string;
  unread: boolean;
  createdAt: string;
}

export interface CompetitiveActivity {
  kind: "competitive";
  sessionId: string;
  themeLabel: string;
  score: number;
  createdAt: string;
}

export interface SqlDojoActivity {
  kind: "sql_dojo";
  sessionId: string;
  themeTitle: string;
  score: number;
  createdAt: string;
}

export type ActivityItem =
  | QuizActivity
  | FeedbackActivity
  | CompetitiveActivity
  | SqlDojoActivity;

export interface CompetitiveStats {
  totalCount: number | null;
  avgScore: number | null;
}

export interface SqlDojoStats {
  totalCount: number | null;
  avgScore: number | null;
}

export interface DashboardData {
  stats: DashboardStats | null;
  competitiveStats: CompetitiveStats;
  sqlDojoStats: SqlDojoStats;
  roadmaps: RoadmapListItem[];
  totalRoadmapCount: number;
  activity: ActivityItem[];
  errorUpdatedAt: number;
  isLoading: boolean;
  isError: boolean;
  /** True when roadmap list is loaded and has 0 items (show welcome state) */
  isEmpty: boolean;
  refetch: () => void;
}

// ---------------------------------------------------------------------------
// Tree helpers
// ---------------------------------------------------------------------------

function flattenDetailNodes(nodes: RoadmapTreeNode[]): RoadmapTreeNode[] {
  const result: RoadmapTreeNode[] = [];
  function walk(node: RoadmapTreeNode) {
    if (node.level === "detail") result.push(node);
    for (const child of node.children) walk(child);
  }
  for (const node of nodes) walk(node);
  return result;
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

const SEVEN_DAYS_MS = 7 * 24 * 60 * 60 * 1000;
const SUMMARY_LIMIT = 5;
const ACTIVITY_LIMIT = 10;
const FEEDBACK_ACTIVITY_LIMIT = 5;

export function useDashboardData(): DashboardData {
  // 1. Roadmap list
  const roadmapList = useRoadmaps();
  const roadmapItems = useMemo(
    () => roadmapList.data?.items ?? [],
    [roadmapList.data],
  );
  const roadmapIds = useMemo(
    () => roadmapItems.map((r) => r.roadmap_id),
    [roadmapItems],
  );

  // 2. Roadmap details (parallel fetch for quiz activity)
  // GET /roadmaps doesn't return tree data, so we fetch each detail.
  // Query keys ["roadmap", id] are shared with the roadmap detail page cache.
  const detailQueries = useQueries({
    queries: roadmapIds.map((id) => ({
      queryKey: ["roadmap", id] as const,
      queryFn: async (): Promise<RoadmapTree> => {
        const res = await apiFetch(`/roadmaps/${id}`);
        return res.json() as Promise<RoadmapTree>;
      },
    })),
  });

  // 3. Competitive sessions (for activity timeline)
  const competitiveQuery = useCompetitiveSessions();
  const sqlDojoQuery = useSqlDojoSessions();

  // 4. Unread feedbacks (provides both total_count for stat card and items
  //    for activity timeline). Key uses "feedbacks" prefix so that
  //    use-mark-as-read's invalidateQueries({ queryKey: ["feedbacks"] })
  //    triggers a refetch. The key shape differs from useFeedbacks()
  //    intentionally — the dashboard fetches unread-only without date filters.
  const feedbacksQuery = useQuery({
    queryKey: ["feedbacks", { read_status: "unread" }] as const,
    queryFn: async (): Promise<FeedbackListResponse> => {
      const res = await apiFetch("/ingestion/feedbacks?read_status=unread");
      return res.json() as Promise<FeedbackListResponse>;
    },
    staleTime: 60_000,
  });

  // ---------------------------------------------------------------------------
  // Derived state
  // ---------------------------------------------------------------------------

  const allDetailsLoaded =
    roadmapIds.length === 0 || detailQueries.every((q) => !q.isLoading);
  const isLoading =
    roadmapList.isLoading ||
    !allDetailsLoaded ||
    feedbacksQuery.isLoading ||
    competitiveQuery.isLoading ||
    sqlDojoQuery.isLoading;
  const isError =
    roadmapList.isError ||
    detailQueries.some((q) => q.isError) ||
    feedbacksQuery.isError ||
    competitiveQuery.isError ||
    sqlDojoQuery.isError;
  const isEmpty =
    !roadmapList.isLoading && roadmapItems.length === 0 && !roadmapList.isError;
  const errorUpdatedAt = Math.max(
    roadmapList.errorUpdatedAt,
    feedbacksQuery.errorUpdatedAt,
    competitiveQuery.errorUpdatedAt,
    sqlDojoQuery.errorUpdatedAt,
    ...detailQueries.map((q) => q.errorUpdatedAt),
  );

  // Collect all detail trees that have loaded successfully
  const detailTrees = useMemo(
    () =>
      detailQueries
        .map((q) => q.data)
        .filter((d): d is RoadmapTree => d != null),
    [detailQueries],
  );
  const latestTreeDataUpdatedAt = useMemo(
    () => Math.max(0, ...detailQueries.map((q) => q.dataUpdatedAt)),
    [detailQueries],
  );
  const unreadFeedbackItems = useMemo(
    () => feedbacksQuery.data?.items ?? [],
    [feedbacksQuery.data],
  );
  const competitiveSessions = useMemo(
    () => competitiveQuery.data?.sessions ?? [],
    [competitiveQuery.data],
  );
  const sqlDojoSessions = useMemo(
    () => sqlDojoQuery.data?.sessions ?? [],
    [sqlDojoQuery.data],
  );

  // Stats
  const stats = useMemo<DashboardStats | null>(() => {
    if (roadmapList.isLoading) return null;
    if (roadmapList.isError && roadmapItems.length === 0) return null;

    const roadmapCount = roadmapList.data?.total_count ?? 0;

    const avgScore =
      roadmapItems.length > 0
        ? Math.floor(
            roadmapItems.reduce((s, r) => s + r.overall_score, 0) /
              roadmapItems.length,
          )
        : null;

    const unreadCount = feedbacksQuery.data?.total_count ?? 0;

    // Use the most recent successful data fetch time as the reference point.
    const cutoff = latestTreeDataUpdatedAt - SEVEN_DAYS_MS;
    let recentQuizCount = 0;
    for (const tree of detailTrees) {
      const details = flattenDetailNodes(tree.items);
      for (const node of details) {
        if (
          latestTreeDataUpdatedAt > 0 &&
          node.last_quiz_at != null &&
          new Date(node.last_quiz_at).getTime() >= cutoff
        ) {
          recentQuizCount++;
        }
      }
    }

    return {
      roadmapCount,
      avgScore,
      unreadCount,
      recentQuizCount,
    };
  }, [
    roadmapList.isLoading,
    roadmapList.isError,
    roadmapList.data,
    roadmapItems,
    feedbacksQuery.data,
    detailTrees,
    latestTreeDataUpdatedAt,
  ]);

  // Roadmap summary (top N)
  const roadmaps = useMemo(
    () => roadmapItems.slice(0, SUMMARY_LIMIT),
    [roadmapItems],
  );

  const totalRoadmapCount = roadmapList.data?.total_count ?? 0;

  // Activity timeline
  const activity = useMemo<ActivityItem[]>(() => {
    // Quiz activities from detail trees
    const quizItems: QuizActivity[] = [];
    for (const tree of detailTrees) {
      const details = flattenDetailNodes(tree.items);
      for (const node of details) {
        if (node.last_quiz_at != null) {
          quizItems.push({
            kind: "quiz",
            itemId: node.id,
            title: node.title,
            score: node.score,
            roadmapId: tree.roadmap_id,
            lastQuizAt: node.last_quiz_at,
          });
        }
      }
    }

    // Feedback activities — limit to 5 items per spec before merging
    const recentFeedbacks = [...unreadFeedbackItems]
      .sort(
        (a, b) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      )
      .slice(0, FEEDBACK_ACTIVITY_LIMIT);

    const feedbackActivities: FeedbackActivity[] = recentFeedbacks.map(
      (f: FeedbackListItem) => ({
        kind: "feedback" as const,
        id: f.id,
        title: f.title,
        unread: !f.is_read,
        createdAt: f.created_at,
      }),
    );

    // Competitive activities
    const competitiveItems: CompetitiveActivity[] = competitiveSessions
      .filter((s) => s.status === "completed" && s.score != null)
      .map((s) => ({
        kind: "competitive" as const,
        sessionId: s.session_id,
        themeLabel: s.theme_label,
        score: s.score!,
        createdAt: s.created_at,
      }));

    const sqlDojoItems: SqlDojoActivity[] = sqlDojoSessions
      .filter((s: SqlDojoSessionListItem) => s.status === "completed" && s.score != null)
      .map((s: SqlDojoSessionListItem) => ({
        kind: "sql_dojo" as const,
        sessionId: s.session_id,
        themeTitle: s.theme_title,
        score: s.score!,
        createdAt: s.created_at,
      }));

    // Merge by timestamp descending
    const merged: ActivityItem[] = [
      ...quizItems,
      ...feedbackActivities,
      ...competitiveItems,
      ...sqlDojoItems,
    ];
    merged.sort((a, b) => {
      const getTime = (item: ActivityItem) => {
        if (item.kind === "quiz") return new Date(item.lastQuizAt).getTime();
        return new Date(item.createdAt).getTime();
      };
      return getTime(b) - getTime(a);
    });

    return merged.slice(0, ACTIVITY_LIMIT);
  }, [detailTrees, unreadFeedbackItems, competitiveSessions, sqlDojoSessions]);

  // Refetch all
  const refetch = useCallback(() => {
    void roadmapList.refetch();
    for (const q of detailQueries) {
      void q.refetch();
    }
    void feedbacksQuery.refetch();
    void competitiveQuery.refetch();
    void sqlDojoQuery.refetch();
  }, [roadmapList, detailQueries, feedbacksQuery, competitiveQuery, sqlDojoQuery]);

  const competitiveStats = useMemo<CompetitiveStats>(() => {
    if (competitiveQuery.isLoading || !competitiveQuery.data) {
      return { totalCount: null, avgScore: null };
    }
    const sessions = competitiveQuery.data.sessions;
    const completed = sessions.filter((s) => s.status === "completed");
    return {
      totalCount: sessions.length,
      avgScore:
        completed.length > 0
          ? Math.round(
              completed.reduce((sum, s) => sum + (s.score ?? 0), 0) /
                completed.length,
            )
          : null,
    };
  }, [competitiveQuery.isLoading, competitiveQuery.data]);

  const sqlDojoStats = useMemo<SqlDojoStats>(() => {
    if (sqlDojoQuery.isLoading || !sqlDojoQuery.data) {
      return { totalCount: null, avgScore: null };
    }
    const sessions = sqlDojoQuery.data.sessions;
    const completed = sessions.filter((s) => s.status === "completed");
    return {
      totalCount: sessions.length,
      avgScore:
        completed.length > 0
          ? Math.round(
              completed.reduce((sum, s) => sum + (s.score ?? 0), 0) /
                completed.length,
            )
          : null,
    };
  }, [sqlDojoQuery.isLoading, sqlDojoQuery.data]);

  return {
    stats,
    competitiveStats,
    sqlDojoStats,
    roadmaps,
    totalRoadmapCount,
    activity,
    errorUpdatedAt,
    isLoading,
    isError,
    isEmpty,
    refetch,
  };
}
