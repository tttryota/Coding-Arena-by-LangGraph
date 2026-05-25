import { screen } from "@testing-library/react";
import { Routes, Route } from "react-router-dom";
import { renderWithProviders, mockJsonResponse } from "@/test-utils";
import { apiFetch, ApiError } from "@/lib/api";
import { RoadmapDetailPage } from "./roadmap-detail-page";
import { useTreeStore } from "./use-tree-store";
import type { RoadmapTree, FeedbackListResponse } from "@/types/api";

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return { ...actual, apiFetch: vi.fn() };
});

const emptyFeedbacks: FeedbackListResponse = { items: [], total_count: 0 };

const roadmapTree: RoadmapTree = {
  roadmap_id: "rm-1",
  topic: "TypeScript基礎",
  overall_score: 65,
  items: [
    {
      id: "n-1",
      title: "型システム",
      description: "TypeScriptの型システムの基礎",
      level: "major",
      score: 65,
      order: 0,
      last_quiz_at: null,
      children: [
        {
          id: "n-2",
          title: "基本型",
          description: "",
          level: "middle",
          score: 70,
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
              last_quiz_at: "2026-05-20T10:00:00+09:00",
              children: [],
            },
          ],
        },
      ],
    },
  ],
};

const emptyTree: RoadmapTree = {
  roadmap_id: "rm-1",
  topic: "TypeScript基礎",
  overall_score: 0,
  items: [],
};

function renderPage() {
  return renderWithProviders(
    <Routes>
      <Route path="/roadmaps/:roadmapId" element={<RoadmapDetailPage />} />
    </Routes>,
    { initialEntries: ["/roadmaps/rm-1"] },
  );
}

function mockSuccess(tree: RoadmapTree = roadmapTree) {
  vi.mocked(apiFetch).mockImplementation(async (path: string) => {
    if (path === "/roadmaps/rm-1") return mockJsonResponse(tree);
    if (path.includes("/ingestion/feedbacks"))
      return mockJsonResponse(emptyFeedbacks);
    throw new Error(`Unexpected path: ${path}`);
  });
}

beforeEach(() => {
  vi.mocked(apiFetch).mockReset();
  useTreeStore.setState({
    initializedFor: null,
    expandedIds: new Set<string>(),
  });
});

describe("RoadmapDetailPage", () => {
  it("ローディング中はスケルトンを表示する", () => {
    vi.mocked(apiFetch).mockImplementation(() => new Promise(() => {}));
    renderPage();

    // タイトルプレースホルダー（animate-pulse の div）
    expect(document.querySelector(".animate-pulse")).toBeInTheDocument();
  });

  it("データがあればツリーを表示する", async () => {
    mockSuccess();
    renderPage();

    // トピック名（h1）
    expect(
      await screen.findByRole("heading", { name: "TypeScript基礎" }),
    ).toBeInTheDocument();
    // majorノードタイトル
    expect(screen.getByText("型システム")).toBeInTheDocument();
    // ヘッダーの「大枠を追加」ボタン
    expect(screen.getByText("大枠を追加")).toBeInTheDocument();
  });

  it("ツリーが空ならDetailEmptyStateを表示する", async () => {
    mockSuccess(emptyTree);
    renderPage();

    expect(
      await screen.findByText("まだ項目がありません"),
    ).toBeInTheDocument();
  });

  it("404エラー時は「見つかりません」を表示する", async () => {
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      if (path.includes("/ingestion/feedbacks"))
        return mockJsonResponse(emptyFeedbacks);
      throw new ApiError(404, "not found");
    });
    renderPage();

    expect(
      await screen.findByText("ロードマップが見つかりません"),
    ).toBeInTheDocument();
    expect(screen.getByText("ロードマップ一覧へ")).toBeInTheDocument();
  });

  it("汎用エラー時は再読み込みを表示する", async () => {
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      if (path.includes("/ingestion/feedbacks"))
        return mockJsonResponse(emptyFeedbacks);
      throw new ApiError(500, "server error");
    });
    renderPage();

    expect(
      await screen.findByText("読み込みに失敗しました"),
    ).toBeInTheDocument();
    expect(screen.getByText("再読み込み")).toBeInTheDocument();
  });
});
