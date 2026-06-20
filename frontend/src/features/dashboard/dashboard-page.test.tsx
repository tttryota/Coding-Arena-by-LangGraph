import { screen } from "@testing-library/react";
import { renderWithProviders, mockJsonResponse } from "@/test-utils";
import { apiFetch, ApiError } from "@/lib/api";
import { DashboardPage } from "./dashboard-page";
import type {
  RoadmapListResponse,
  RoadmapTree,
  FeedbackListResponse,
} from "@/types/api";

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return { ...actual, apiFetch: vi.fn() };
});

const now = new Date();
const recentDate = new Date(now.getTime() - 2 * 24 * 60 * 60 * 1000);

const roadmapList: RoadmapListResponse = {
  items: [
    { roadmap_id: "rm-1", topic: "TypeScript基礎", overall_score: 72 },
    { roadmap_id: "rm-2", topic: "React設計パターン", overall_score: 48 },
  ],
  total_count: 2,
};

const roadmapTree1: RoadmapTree = {
  roadmap_id: "rm-1",
  topic: "TypeScript基礎",
  overall_score: 72,
  items: [
    {
      id: "n-1",
      title: "型システム",
      description: "",
      level: "major",
      score: 72,
      order: 0,
      last_quiz_at: null,
      children: [
        {
          id: "n-2",
          title: "基本型",
          description: "",
          level: "middle",
          score: 72,
          order: 0,
          last_quiz_at: null,
          children: [
            {
              id: "n-3",
              title: "string / number / boolean",
              description: "",
              level: "detail",
              score: 80,
              order: 0,
              last_quiz_at: recentDate.toISOString(),
              children: [],
            },
          ],
        },
      ],
    },
  ],
};

const roadmapTree2: RoadmapTree = {
  roadmap_id: "rm-2",
  topic: "React設計パターン",
  overall_score: 48,
  items: [],
};

const unreadFeedbacks: FeedbackListResponse = {
  items: [
    {
      id: "fb-1",
      source_path: "notes/ts.md",
      roadmap_item_id: null,
      title: "型の説明不正確",
      body: "内容に誤りがあります",
      is_read: false,
      created_at: recentDate.toISOString(),
      read_at: null,
    },
  ],
  total_count: 1,
};

const emptyRoadmapList: RoadmapListResponse = { items: [], total_count: 0 };
const emptyFeedbacks: FeedbackListResponse = { items: [], total_count: 0 };

function mockSuccess(
  roadmaps: RoadmapListResponse = roadmapList,
  feedbacks: FeedbackListResponse = unreadFeedbacks,
) {
  vi.mocked(apiFetch).mockImplementation(async (path: string) => {
    if (path === "/roadmaps") return mockJsonResponse(roadmaps);
    if (path === "/roadmaps/rm-1") return mockJsonResponse(roadmapTree1);
    if (path === "/roadmaps/rm-2") return mockJsonResponse(roadmapTree2);
    if (path.includes("/ingestion/feedbacks"))
      return mockJsonResponse(feedbacks);
    if (path === "/algorithm-quiz/sessions")
      return mockJsonResponse({ sessions: [] });
    if (path === "/sql-dojo/sessions")
      return mockJsonResponse({ sessions: [] });
    throw new Error(`Unexpected path: ${path}`);
  });
}

beforeEach(() => {
  vi.mocked(apiFetch).mockReset();
});

describe("DashboardPage", () => {
  /*
   * テスト対象: DashboardPage コンポーネント。
   * テストケース: 個別条件での処理を検証する。
   * 期待結果: 想定どおりの処理結果が得られる。
   */
  it("ローディング中はスケルトンを表示する", () => {
    vi.mocked(apiFetch).mockImplementation(() => new Promise(() => {}));
    renderWithProviders(<DashboardPage />);

    expect(screen.getByText("読み込み中…")).toBeInTheDocument();
  });

  /*
   * テスト対象: DashboardPage コンポーネント。
   * テストケース: 個別条件での処理を検証する。
   * 期待結果: 想定どおりの処理結果が得られる。
   */
  it("データがあればスタッツとロードマップを表示する", async () => {
    mockSuccess();
    renderWithProviders(<DashboardPage />);

    // 副題
    expect(
      await screen.findByText(
        "学習の全体像と次にやることをここで決めます",
      ),
    ).toBeInTheDocument();
    // ロードマップ数
    expect(screen.getByText("学習中のロードマップ")).toBeInTheDocument();
    // 未読フィードバック
    expect(screen.getByText("未読フィードバック")).toBeInTheDocument();
    expect(screen.getByText("SQL道場(直近)")).toBeInTheDocument();
  });

  /*
   * テスト対象: DashboardPage コンポーネント。
   * テストケース: 個別条件での処理を検証する。
   * 期待結果: 想定どおりの処理結果が得られる。
   */
  it("ロードマップが空なら Welcome を表示する", async () => {
    mockSuccess(emptyRoadmapList, emptyFeedbacks);
    renderWithProviders(<DashboardPage />);

    expect(
      await screen.findByText("学習を始めましょう"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("ロードマップを作成する"),
    ).toBeInTheDocument();
  });

  /*
   * テスト対象: DashboardPage コンポーネント。
   * テストケース: 個別条件での処理を検証する。
   * 期待結果: 想定どおりの処理結果が得られる。
   */
  it("エラー時はToastを表示する", async () => {
    vi.mocked(apiFetch).mockImplementation(async () => {
      throw new ApiError(500, "server error");
    });
    renderWithProviders(<DashboardPage />);

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(
      "ダッシュボードの取得に失敗しました",
    );
    expect(screen.getByText("再読み込み")).toBeInTheDocument();
  });

  it("SQL道場一覧だけ失敗してもダッシュボード本体は表示する", async () => {
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      if (path === "/roadmaps") return mockJsonResponse(roadmapList);
      if (path === "/roadmaps/rm-1") return mockJsonResponse(roadmapTree1);
      if (path === "/roadmaps/rm-2") return mockJsonResponse(roadmapTree2);
      if (path.includes("/ingestion/feedbacks")) {
        return mockJsonResponse(unreadFeedbacks);
      }
      if (path === "/algorithm-quiz/sessions") {
        return mockJsonResponse({ sessions: [] });
      }
      if (path === "/sql-dojo/sessions") {
        throw new ApiError(500, "sql dojo failed");
      }
      throw new Error(`Unexpected path: ${path}`);
    });

    renderWithProviders(<DashboardPage />);

    expect(
      await screen.findByText("学習の全体像と次にやることをここで決めます"),
    ).toBeInTheDocument();
    expect(screen.getByText("SQL道場(直近)")).toBeInTheDocument();
    expect(screen.getByText("取得失敗")).toBeInTheDocument();
  });
});
