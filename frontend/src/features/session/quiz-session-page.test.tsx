import { screen } from "@testing-library/react";
import { Routes, Route } from "react-router-dom";
import { renderWithProviders, mockJsonResponse } from "@/test-utils";
import { apiFetch, ApiError } from "@/lib/api";
import { QuizSessionPage } from "./quiz-session-page";
import { useQuizSessionStore } from "./use-quiz-session-store";
import type { SessionDetailResponse, FeedbackListResponse } from "@/types/api";

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return { ...actual, apiFetch: vi.fn() };
});

const emptyFeedbacks: FeedbackListResponse = { items: [], total_count: 0 };

const sessionDetail: SessionDetailResponse = {
  session_id: "sess-1",
  session: {
    id: "sess-1",
    roadmap_item_id: "ri-1",
    status: "in_progress",
    completed_at: null,
  },
};

const completedSession: SessionDetailResponse = {
  session_id: "sess-1",
  session: {
    id: "sess-1",
    roadmap_item_id: "ri-1",
    status: "completed",
    completed_at: "2026-05-25T10:00:00+09:00",
  },
};

function renderPage() {
  return renderWithProviders(
    <Routes>
      <Route path="/sessions/:sessionId" element={<QuizSessionPage />} />
    </Routes>,
    {
      initialEntries: [
        {
          pathname: "/sessions/sess-1",
          state: { topic: "TypeScript基礎", roadmapId: "rm-1" },
        },
      ],
    },
  );
}

function mockSuccess(detail: SessionDetailResponse = sessionDetail) {
  vi.mocked(apiFetch).mockImplementation(async (path: string) => {
    if (path === "/sessions/sess-1") return mockJsonResponse(detail);
    if (path.includes("/ingestion/feedbacks"))
      return mockJsonResponse(emptyFeedbacks);
    throw new Error(`Unexpected path: ${path}`);
  });
}

beforeEach(() => {
  vi.mocked(apiFetch).mockReset();
  useQuizSessionStore.getState().reset();
});

describe("QuizSessionPage", () => {
  it("ローディング中はスケルトンを表示する", () => {
    vi.mocked(apiFetch).mockImplementation(() => new Promise(() => {}));
    renderPage();

    // スケルトンの animate-pulse 要素が存在する
    expect(document.querySelector(".animate-pulse")).toBeInTheDocument();
  });

  it("質問フェーズを表示する", async () => {
    mockSuccess();

    // セッション状態をプリセット（APIレスポンスに含まれない追加フィールド）
    useQuizSessionStore.setState({
      phase: "question",
      sessionState: {
        session_id: "sess-1",
        roadmap_item_id: "ri-1",
        roadmap_item_level: "detail",
        roadmap_item_title: "string / number / boolean",
        roadmap_item_description: "",
        is_resumed: false,
        confirmation_points: [
          { id: "cp-1", content: "基本型の理解", format: "knowledge" },
        ],
        current_point_index: 0,
        current_question_text: "TypeScriptのstring型について説明してください",
        current_answer_type: "textarea",
        total_questions_asked: 1,
      },
    });

    renderPage();

    // 問題テキスト
    expect(
      await screen.findByText(
        "TypeScriptのstring型について説明してください",
      ),
    ).toBeInTheDocument();
    // 回答ボタン
    expect(screen.getByText("回答する")).toBeInTheDocument();
    // 解説ボタン
    expect(
      screen.getByRole("button", { name: /解説して/ }),
    ).toBeInTheDocument();
  });

  it("完了セッションはサマリーフェーズを表示する", async () => {
    mockSuccess(completedSession);

    // サマリーフェーズ用の回答データをプリセット
    useQuizSessionStore.setState({
      phase: "summary",
      sessionState: {
        session_id: "sess-1",
        roadmap_item_id: "ri-1",
        roadmap_item_level: "detail",
        roadmap_item_title: "string / number / boolean",
        roadmap_item_description: "",
        is_resumed: false,
        answers: [
          {
            question_number: 1,
            confirmation_point_id: "cp-1",
            question_text: "string型について説明してください",
            answer_type: "textarea",
            answer_text: "文字列を表す型です",
            score: 75,
            feedback: "概ね正確です",
          },
        ],
      },
    });

    renderPage();

    expect(await screen.findByText("セッション完了")).toBeInTheDocument();
    expect(screen.getByText("お疲れさまでした")).toBeInTheDocument();
    expect(screen.getByText("ロードマップに戻る")).toBeInTheDocument();
  });

  it("404エラー時は「見つかりません」を表示する", async () => {
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      if (path.includes("/ingestion/feedbacks"))
        return mockJsonResponse(emptyFeedbacks);
      throw new ApiError(404, "not found");
    });
    renderPage();

    expect(
      await screen.findByText("セッションが見つかりません"),
    ).toBeInTheDocument();
    expect(screen.getByText("ロードマップへ")).toBeInTheDocument();
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
