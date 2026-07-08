import { screen, waitFor } from "@testing-library/react";
import { renderWithProviders, mockJsonResponse } from "@/test-utils";
import { apiFetch, ApiError } from "@/lib/api";
import { RoadmapListPage } from "./roadmap-list-page";
import type { RoadmapListResponse } from "@/types/api";

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return { ...actual, apiFetch: vi.fn() };
});

const roadmapList: RoadmapListResponse = {
  items: [
    { roadmap_id: "rm-1", topic: "TypeScript基礎", overall_score: 72 },
    { roadmap_id: "rm-2", topic: "React設計パターン", overall_score: 45 },
    { roadmap_id: "rm-3", topic: "データベース入門", overall_score: 30 },
  ],
  total_count: 3,
};

const emptyRoadmapList: RoadmapListResponse = { items: [], total_count: 0 };

function renderPage() {
  return renderWithProviders(<RoadmapListPage />, {
    initialEntries: ["/roadmaps"],
  });
}

function mockSuccess(roadmaps: RoadmapListResponse = roadmapList) {
  vi.mocked(apiFetch).mockImplementation(async (path: string) => {
    if (path === "/roadmaps") return mockJsonResponse(roadmaps);
    throw new Error(`Unexpected path: ${path}`);
  });
}

beforeEach(() => {
  vi.mocked(apiFetch).mockReset();
});

describe("RoadmapListPage", () => {
  /*
   * テスト対象: RoadmapListPage コンポーネント。
   * テストケース: 個別条件での処理を検証する。
   * 期待結果: 想定どおりの処理結果が得られる。
   */
  it("ローディング中はスケルトンを表示する", () => {
    vi.mocked(apiFetch).mockImplementation(() => new Promise(() => {}));
    renderPage();

    expect(screen.getByText("読み込み中…")).toBeInTheDocument();
  });

  /*
   * テスト対象: RoadmapListPage コンポーネント。
   * テストケース: 個別条件での処理を検証する。
   * 期待結果: 想定どおりの処理結果が得られる。
   */
  it("データがあればロードマップカードを表示する", async () => {
    mockSuccess();
    renderPage();

    expect(await screen.findByText("TypeScript基礎")).toBeInTheDocument();
    expect(screen.getByText("React設計パターン")).toBeInTheDocument();
    expect(screen.getByText("データベース入門")).toBeInTheDocument();
    expect(
      screen.getByText("3 件のロードマップ・作成順"),
    ).toBeInTheDocument();
    expect(screen.getByText("新規作成")).toBeInTheDocument();
  });

  /*
   * テスト対象: RoadmapListPage コンポーネント。
   * テストケース: 個別条件での処理を検証する。
   * 期待結果: 想定どおりの処理結果が得られる。
   */
  it("データが空なら空状態を表示する", async () => {
    mockSuccess(emptyRoadmapList);
    renderPage();

    expect(
      await screen.findByText("ロードマップがまだありません"),
    ).toBeInTheDocument();
  });

  /*
   * テスト対象: RoadmapListPage コンポーネント。
   * テストケース: 個別条件での処理を検証する。
   * 期待結果: 想定どおりの処理結果が得られる。
   */
  it("エラー時はエラーメッセージと再読み込みボタンを表示する", async () => {
    vi.mocked(apiFetch).mockImplementation(async () => {
      throw new ApiError(500, "server error");
    });
    renderPage();

    expect(
      await screen.findByText("ロードマップの読み込みに失敗しました"),
    ).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText("再読み込み")).toBeInTheDocument();
    });
  });
});
