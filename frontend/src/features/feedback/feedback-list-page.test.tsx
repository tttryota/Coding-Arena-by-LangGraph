import { screen } from "@testing-library/react";
import { renderWithProviders, mockJsonResponse } from "@/test-utils";
import { apiFetch, ApiError } from "@/lib/api";
import { FeedbackListPage } from "./feedback-list-page";
import { useFeedbackFilters } from "./use-feedback-filters";
import type { FeedbackListResponse } from "@/types/api";

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return { ...actual, apiFetch: vi.fn() };
});

const feedbackList: FeedbackListResponse = {
  items: [
    {
      id: "fb-1",
      source_path: "notes/typescript.md",
      roadmap_item_id: "ri-1",
      title: "型システムの説明が不正確",
      body: "【正確性】\n内容に一部誤りがあります",
      is_read: false,
      created_at: "2026-05-24T10:00:00+09:00",
      read_at: null,
    },
    {
      id: "fb-2",
      source_path: "notes/react.md",
      roadmap_item_id: null,
      title: "Hooks の使い方に改善点",
      body: "【改善提案】\nカスタムフックの分離を推奨",
      is_read: true,
      created_at: "2026-05-23T08:00:00+09:00",
      read_at: "2026-05-23T12:00:00+09:00",
    },
    {
      id: "fb-3",
      source_path: "notes/db.md",
      roadmap_item_id: null,
      title: "インデックスの解説が不足",
      body: "【改善提案】\nB-Treeインデックスの説明を追加してください",
      is_read: false,
      created_at: "2026-05-22T15:00:00+09:00",
      read_at: null,
    },
  ],
  total_count: 3,
};

const emptyFeedbacks: FeedbackListResponse = { items: [], total_count: 0 };

function mockSuccess(data: FeedbackListResponse = feedbackList) {
  vi.mocked(apiFetch).mockImplementation(async (path: string) => {
    if (path.includes("/ingestion/feedbacks"))
      return mockJsonResponse(data);
    throw new Error(`Unexpected path: ${path}`);
  });
}

beforeEach(() => {
  vi.mocked(apiFetch).mockReset();
  useFeedbackFilters.setState({
    dateFrom: null,
    dateTo: null,
    readStatus: "all",
  });
});

describe("FeedbackListPage", () => {
  it("ローディング中はスケルトンを表示する", () => {
    vi.mocked(apiFetch).mockImplementation(() => new Promise(() => {}));
    renderWithProviders(<FeedbackListPage />, {
      initialEntries: ["/feedbacks"],
    });

    expect(screen.getByText("読み込み中…")).toBeInTheDocument();
  });

  it("データがあればフィードバックカードを表示する", async () => {
    mockSuccess();
    renderWithProviders(<FeedbackListPage />, {
      initialEntries: ["/feedbacks"],
    });

    expect(
      await screen.findByText("型システムの説明が不正確"),
    ).toBeInTheDocument();
    expect(screen.getByText("Hooks の使い方に改善点")).toBeInTheDocument();
    expect(screen.getByText("インデックスの解説が不足")).toBeInTheDocument();
    // 未読バッジ
    expect(screen.getByText("未読 2")).toBeInTheDocument();
    // すべて既読にするボタン
    expect(screen.getByText("すべて既読にする")).toBeInTheDocument();
  });

  it("データが空（フィルタなし）なら空状態を表示する", async () => {
    mockSuccess(emptyFeedbacks);
    renderWithProviders(<FeedbackListPage />, {
      initialEntries: ["/feedbacks"],
    });

    expect(
      await screen.findByText("フィードバックはまだありません"),
    ).toBeInTheDocument();
  });

  it("フィルタ適用で結果0件なら「条件に一致しない」を表示する", async () => {
    useFeedbackFilters.setState({ readStatus: "unread" });
    mockSuccess(emptyFeedbacks);
    renderWithProviders(<FeedbackListPage />, {
      initialEntries: ["/feedbacks"],
    });

    expect(
      await screen.findByText("条件に一致するフィードバックはありません"),
    ).toBeInTheDocument();
    const resetButtons = screen.getAllByRole("button", { name: /リセット/ });
    expect(resetButtons.length).toBeGreaterThanOrEqual(1);
  });

  it("エラー時はToastを表示する", async () => {
    vi.mocked(apiFetch).mockImplementation(async () => {
      throw new ApiError(500, "server error");
    });
    renderWithProviders(<FeedbackListPage />, {
      initialEntries: ["/feedbacks"],
    });

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(
      "フィードバック一覧の取得に失敗しました",
    );
    expect(screen.getByText("再読み込み")).toBeInTheDocument();
  });
});
