import { useMemo, useCallback } from "react";
import { useQueries } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { useRoadmaps } from "@/features/roadmap/use-roadmaps";
import { useCompetitiveSessions } from "@/features/competitive/use-competitive";
import { useAlgorithmFoundationSessions } from "@/features/algorithm-foundations/use-algorithm-foundations";
import { useSqlDojoSessions } from "@/features/sql-dojo/use-sql-dojo";
import type {
  AlgorithmFoundationSessionListItem,
  RoadmapListItem,
  RoadmapTree,
  RoadmapTreeNode,
  SqlDojoSessionListItem,
} from "@/types/api";

// ---------------------------------------------------------------------------
// Public types
// ---------------------------------------------------------------------------

export interface DashboardStats {
  roadmapCount: number;
  avgScore: number | null;
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
  topicTitle: string | null;
  score: number;
  createdAt: string;
}

export interface AlgorithmFoundationsActivity {
  kind: "algorithm_foundations";
  sessionId: string;
  unitTitle: string;
  score: number;
  createdAt: string;
}

export type ActivityItem =
  | QuizActivity
  | CompetitiveActivity
  | AlgorithmFoundationsActivity
  | SqlDojoActivity;

export interface CompetitiveStats {
  totalCount: number | null;
  avgScore: number | null;
  isError: boolean;
}

export interface SqlDojoStats {
  totalCount: number | null;
  avgScore: number | null;
  isError: boolean;
}

export interface AlgorithmFoundationsStats {
  totalCount: number | null;
  avgScore: number | null;
  isError: boolean;
}

export interface DashboardData {
  stats: DashboardStats | null;
  competitiveStats: CompetitiveStats;
  algorithmFoundationsStats: AlgorithmFoundationsStats;
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
  const algorithmFoundationsQuery = useAlgorithmFoundationSessions();
  const sqlDojoQuery = useSqlDojoSessions();

  const allDetailsLoaded =
    roadmapIds.length === 0 || detailQueries.every((q) => !q.isLoading);
  const isLoading = roadmapList.isLoading || !allDetailsLoaded;
  const isError = roadmapList.isError || detailQueries.some((q) => q.isError);
  const isEmpty =
    !roadmapList.isLoading && roadmapItems.length === 0 && !roadmapList.isError;
  const errorUpdatedAt = Math.max(
    roadmapList.errorUpdatedAt,
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
  const competitiveSessions = useMemo(
    () => competitiveQuery.data?.sessions ?? [],
    [competitiveQuery.data],
  );
  const sqlDojoSessions = useMemo(
    () => sqlDojoQuery.data?.sessions ?? [],
    [sqlDojoQuery.data],
  );
  const algorithmFoundationSessions = useMemo(
    () => algorithmFoundationsQuery.data?.sessions ?? [],
    [algorithmFoundationsQuery.data],
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
      recentQuizCount,
    };
  }, [
    roadmapList.isLoading,
    roadmapList.isError,
    roadmapList.data,
    roadmapItems,
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
        topicTitle: s.topic_title,
        score: s.score!,
        createdAt: s.created_at,
      }));

    const algorithmFoundationsItems: AlgorithmFoundationsActivity[] =
      algorithmFoundationSessions
        .filter(
          (s: AlgorithmFoundationSessionListItem) =>
            s.status === "completed" && s.score != null,
        )
        .map((s: AlgorithmFoundationSessionListItem) => ({
          kind: "algorithm_foundations" as const,
          sessionId: s.session_id,
          unitTitle: s.unit_title,
          score: s.score!,
          createdAt: s.created_at,
        }));

    // Merge by timestamp descending
    const merged: ActivityItem[] = [
      ...quizItems,
      ...competitiveItems,
      ...algorithmFoundationsItems,
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
  }, [
    detailTrees,
    competitiveSessions,
    algorithmFoundationSessions,
    sqlDojoSessions,
  ]);

  // Refetch all
  const refetch = useCallback(() => {
    void roadmapList.refetch();
    for (const q of detailQueries) {
      void q.refetch();
    }
    void competitiveQuery.refetch();
    void algorithmFoundationsQuery.refetch();
    void sqlDojoQuery.refetch();
  }, [
    roadmapList,
    detailQueries,
    competitiveQuery,
    algorithmFoundationsQuery,
    sqlDojoQuery,
  ]);

  const competitiveStats = useMemo<CompetitiveStats>(() => {
    if (competitiveQuery.isError && !competitiveQuery.data) {
      return { totalCount: null, avgScore: null, isError: true };
    }
    if (competitiveQuery.isLoading || !competitiveQuery.data) {
      return { totalCount: null, avgScore: null, isError: false };
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
      isError: false,
    };
  }, [competitiveQuery.isError, competitiveQuery.isLoading, competitiveQuery.data]);

  const sqlDojoStats = useMemo<SqlDojoStats>(() => {
    if (sqlDojoQuery.isError && !sqlDojoQuery.data) {
      return { totalCount: null, avgScore: null, isError: true };
    }
    if (sqlDojoQuery.isLoading || !sqlDojoQuery.data) {
      return { totalCount: null, avgScore: null, isError: false };
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
      isError: false,
    };
  }, [sqlDojoQuery.isError, sqlDojoQuery.isLoading, sqlDojoQuery.data]);

  const algorithmFoundationsStats = useMemo<AlgorithmFoundationsStats>(() => {
    if (algorithmFoundationsQuery.isError && !algorithmFoundationsQuery.data) {
      return { totalCount: null, avgScore: null, isError: true };
    }
    if (
      algorithmFoundationsQuery.isLoading ||
      !algorithmFoundationsQuery.data
    ) {
      return { totalCount: null, avgScore: null, isError: false };
    }
    const sessions = algorithmFoundationsQuery.data.sessions;
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
      isError: false,
    };
  }, [
    algorithmFoundationsQuery.isError,
    algorithmFoundationsQuery.isLoading,
    algorithmFoundationsQuery.data,
  ]);

  return {
    stats,
    competitiveStats,
    algorithmFoundationsStats,
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
