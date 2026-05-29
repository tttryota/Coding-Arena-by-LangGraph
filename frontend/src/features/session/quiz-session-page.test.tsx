import { screen } from "@testing-library/react";
import { Routes, Route } from "react-router-dom";
import { renderWithProviders, mockJsonResponse } from "@/test-utils";
import { apiFetch, ApiError } from "@/lib/api";
import { QuizSessionPage } from "./quiz-session-page";
import { useQuizSessionStore } from "./use-quiz-session-store";
import type {
  SessionDetailResponse,
  FeedbackListResponse,
  CodingSessionStateDTO,
} from "@/types/api";

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
  graph_state: {
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
};

const completedSession: SessionDetailResponse = {
  session_id: "sess-1",
  session: {
    id: "sess-1",
    roadmap_item_id: "ri-1",
    status: "completed",
    completed_at: "2026-05-25T10:00:00+09:00",
  },
  graph_state: {
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
};

const codingSessionDetail: SessionDetailResponse = {
  session_id: "coding-1",
  graph_state: {
    session_id: "coding-1",
    roadmap_item_id: "ri-1",
    roadmap_item_level: "detail",
    roadmap_item_title: "配列操作",
    roadmap_item_description: "mapやfilterを書けるようになる",
    is_resumed: false,
    lecture_content: "配列操作の基礎について...",
    lecture_phase_active: true,
  } satisfies CodingSessionStateDTO,
};

const codingPracticeDetail: SessionDetailResponse = {
  session_id: "coding-2",
  graph_state: {
    session_id: "coding-2",
    roadmap_item_id: "ri-1",
    roadmap_item_level: "detail",
    roadmap_item_title: "配列操作",
    roadmap_item_description: "mapやfilterを書けるようになる",
    is_resumed: false,
    lecture_content: "配列操作の基礎について...",
    lecture_phase_active: false,
    confirmation_points: [
      { id: "cp-1", content: "map関数", start_format: "rewrite", end_format: "implement" },
    ],
    current_point_index: 0,
    current_question_text: "以下のコードを書き換えてください",
    current_example_code: "const arr = [1, 2, 3];",
    current_format: "rewrite",
    total_questions_asked: 1,
  } satisfies CodingSessionStateDTO,
};

function renderPage(sessionId = "sess-1") {
  return renderWithProviders(
    <Routes>
      <Route path="/sessions/:sessionId" element={<QuizSessionPage />} />
    </Routes>,
    {
      initialEntries: [
        {
          pathname: `/sessions/${sessionId}`,
          state: { topic: "TypeScript基礎", roadmapId: "rm-1" },
        },
      ],
    },
  );
}

function mockSuccess(detail: SessionDetailResponse = sessionDetail) {
  vi.mocked(apiFetch).mockImplementation(async (path: string) => {
    if (path === "/sessions/sess-1") return mockJsonResponse(detail);
    if (path === "/sessions/coding-1") return mockJsonResponse(detail);
    if (path === "/sessions/coding-2") return mockJsonResponse(detail);
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
    expect(document.querySelector(".animate-pulse")).toBeInTheDocument();
  });

  it("質問フェーズを表示する", async () => {
    mockSuccess();
    renderPage();

    expect(
      await screen.findByText(
        "TypeScriptのstring型について説明してください",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("回答する")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /解説して/ }),
    ).toBeInTheDocument();
  });

  it("完了セッションはサマリーフェーズを表示する", async () => {
    mockSuccess(completedSession);
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

  // --- Coding session tests ---

  it("コーディングセッション: 座学フェーズを表示する", async () => {
    mockSuccess(codingSessionDetail);
    renderPage("coding-1");

    expect(
      await screen.findByText("配列操作の基礎について..."),
    ).toBeInTheDocument();
    expect(screen.getByText("座学")).toBeInTheDocument();
    expect(screen.getByText("演習を始める")).toBeInTheDocument();
  });

  it("コーディングセッション: 練習フェーズを表示する", async () => {
    mockSuccess(codingPracticeDetail);
    renderPage("coding-2");

    expect(
      await screen.findByText("以下のコードを書き換えてください"),
    ).toBeInTheDocument();
    expect(screen.getAllByText("書き換え").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("const arr = [1, 2, 3];")).toBeInTheDocument();
    expect(screen.getByText("回答する")).toBeInTheDocument();
    // Coding sessions should not show explain button
    expect(screen.queryByRole("button", { name: /解説して/ })).not.toBeInTheDocument();
  });

  it("コーディングセッション: フィードバックフェーズを表示する", async () => {
    mockSuccess(codingPracticeDetail);
    renderPage("coding-2");

    // Wait for hydration to complete (question phase)
    await screen.findByText("以下のコードを書き換えてください");

    // Simulate post-submit state: backend returns next question data + score/feedback
    useQuizSessionStore.setState({
      phase: "feedback",
      codingState: {
        session_id: "coding-2",
        roadmap_item_id: "ri-1",
        roadmap_item_level: "detail",
        roadmap_item_title: "配列操作",
        roadmap_item_description: "mapやfilterを書けるようになる",
        is_resumed: false,
        lecture_phase_active: false,
        current_score: 85,
        current_feedback: "よくできました",
        next_action: "next_step",
        current_format: "fill_blank",
        current_question_text: "次の穴埋め問題",
        total_questions_asked: 2,
        confirmation_points: [
          { id: "cp-1", content: "map関数", start_format: "rewrite", end_format: "implement" },
        ],
        current_point_index: 0,
      },
      codingFeedbackSnapshot: {
        questionText: "以下のコードを書き換えてください",
        questionNumber: 1,
        format: "rewrite",
      },
    });

    expect(await screen.findByText("よくできました")).toBeInTheDocument();
    expect(screen.getAllByText("85").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("難易度が上がります。")).toBeInTheDocument();
    expect(screen.getByText("次の問題へ")).toBeInTheDocument();
    // Snapshot question text is used in feedback display (not the next question)
    expect(screen.queryByText("次の穴埋め問題")).not.toBeInTheDocument();
  });

  it("コーディングセッション: retryアクションを表示する", async () => {
    mockSuccess(codingPracticeDetail);
    renderPage("coding-2");

    await screen.findByText("以下のコードを書き換えてください");

    useQuizSessionStore.setState({
      phase: "feedback",
      codingState: {
        session_id: "coding-2",
        roadmap_item_id: "ri-1",
        roadmap_item_level: "detail",
        roadmap_item_title: "配列操作",
        roadmap_item_description: "mapやfilterを書けるようになる",
        is_resumed: false,
        lecture_phase_active: false,
        current_score: 40,
        current_feedback: "もう少し頑張りましょう",
        next_action: "retry",
        current_format: "bug_fix",
        current_question_text: "バグを修正してください",
        total_questions_asked: 2,
        confirmation_points: [
          { id: "cp-1", content: "map関数", start_format: "rewrite", end_format: "implement" },
        ],
        current_point_index: 0,
      },
      codingFeedbackSnapshot: {
        questionText: "バグを修正してください",
        questionNumber: 2,
        format: "bug_fix",
      },
    });

    expect(await screen.findByText("もう少し頑張りましょう")).toBeInTheDocument();
    expect(screen.getAllByText("40").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("もう一度挑戦しましょう。")).toBeInTheDocument(); // notice card title
    expect(screen.getByText("もう一度挑戦")).toBeInTheDocument();
  });
});
