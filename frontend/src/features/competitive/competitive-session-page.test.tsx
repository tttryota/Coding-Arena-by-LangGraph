import { fireEvent, screen, waitFor } from "@testing-library/react";
import { Route, Routes, useNavigate } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { CompetitiveSessionPage } from "./competitive-session-page";
import { useCompetitiveStore } from "./use-competitive-store";
import { mockJsonResponse, renderWithProviders } from "@/test-utils";
import type {
  CompetitiveAnswerResponse,
  CompetitiveSessionResponse,
} from "@/types/api";

const inProgressSession: CompetitiveSessionResponse = {
  session_id: "sess-1",
  theme_id: "algo-001",
  theme_label: "二分探索",
  theme_category: "探索",
  programming_language: "python",
  problem_statement: "問題文です",
  input_format: "入力形式",
  output_format: "出力形式",
  constraints: "制約",
  examples: [{ input: "1", output: "2" }],
  status: "in_progress",
  created_at: "2026-06-19T00:00:00+09:00",
};

const completedSession: CompetitiveSessionResponse = {
  ...inProgressSession,
  status: "completed",
  score: 88,
  feedback: "よい実装です",
  time_complexity: "O(log N)",
  space_complexity: "O(1)",
  improvement_suggestions: "境界条件の整理を明示するとさらに読みやすいです",
  rubric_scores_json: "[]",
  reference_solution: "def solve():\n    return 42",
};

const submitResult: CompetitiveAnswerResponse = {
  session_id: "sess-1",
  score: 91,
  feedback: "よい解答です",
  time_complexity: "O(log N)",
  space_complexity: "O(1)",
  improvement_suggestions: "変数名を少しだけ整理するとさらに読みやすいです",
  rubric_scores_json: "[]",
  reference_solution: "def solve():\n    return 42",
};

function SessionNavigator() {
  const navigate = useNavigate();
  return (
    <>
      <button type="button" onClick={() => navigate("/algorithm-quiz/sess-1")}>
        go sess-1
      </button>
      <button type="button" onClick={() => navigate("/algorithm-quiz/sess-2")}>
        go sess-2
      </button>
      <Routes>
        <Route
          path="/algorithm-quiz/:sessionId"
          element={<CompetitiveSessionPage />}
        />
      </Routes>
    </>
  );
}

function renderPage(sessionId = "sess-1") {
  return renderWithProviders(<SessionNavigator />, {
    initialEntries: [`/algorithm-quiz/${sessionId}`],
  });
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

afterEach(() => {
  vi.restoreAllMocks();
});

beforeEach(() => {
  useCompetitiveStore.getState().reset();
});

describe("CompetitiveSessionPage", () => {
  it("コード入力欄でTabインデントと質問送信ができる", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = typeof input === "string" ? input : input.toString();
      if (url.endsWith("/api/algorithm-quiz/sessions/sess-1/question")) {
        expect(init?.method).toBe("POST");
        return mockJsonResponse({
          session_id: "sess-1",
          chat_response_text:
            "まずは制約から必要な計算量を見積もるとよいです。",
        });
      }
      if (url.endsWith("/api/algorithm-quiz/sessions/sess-1")) {
        return mockJsonResponse(inProgressSession);
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    renderPage();

    expect(await screen.findByText("問題文です")).toBeInTheDocument();
    const codeTextarea = screen.getByPlaceholderText(
      "# Python で解答を書いてください",
    ) as HTMLTextAreaElement;
    expect(codeTextarea.className).toContain("min-h-[320px]");

    fireEvent.change(codeTextarea, { target: { value: "print(1)" } });
    codeTextarea.setSelectionRange(0, 0);
    fireEvent.keyDown(codeTextarea, { key: "Tab" });
    expect(codeTextarea.value).toBe("  print(1)");

    const chatTextarea = screen.getByPlaceholderText(
      "制約の見方、考える順番、計算量の見積もりなどを質問できます",
    ) as HTMLTextAreaElement;
    fireEvent.change(chatTextarea, {
      target: { value: "どこから考えればいい？" },
    });
    fireEvent.click(screen.getByRole("button", { name: "質問する" }));

    await waitFor(() => {
      expect(
        screen.getByText("まずは制約から必要な計算量を見積もるとよいです。"),
      ).toBeInTheDocument();
    });
    expect(chatTextarea.value).toBe("");
  });

  it("提出直後の結果画面では正解コードを表示する", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = typeof input === "string" ? input : input.toString();
      if (url.endsWith("/api/algorithm-quiz/sessions/sess-1/answer")) {
        return mockJsonResponse(submitResult);
      }
      if (url.endsWith("/api/algorithm-quiz/sessions/sess-1")) {
        return mockJsonResponse(inProgressSession);
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    renderPage();

    const codeTextarea = (await screen.findByPlaceholderText(
      "# Python で解答を書いてください",
    )) as HTMLTextAreaElement;
    fireEvent.change(codeTextarea, {
      target: { value: "def solve():\n    return 42" },
    });
    fireEvent.click(screen.getByRole("button", { name: "提出" }));

    expect(await screen.findByText("結果: 二分探索")).toBeInTheDocument();
    expect(screen.getByText("正解コード")).toBeInTheDocument();
    expect(screen.getByText(/def solve\(\):/)).toBeInTheDocument();
    expect(
      screen.queryByText("問題への質問"),
    ).not.toBeInTheDocument();
  });

  it("完了済みセッション再訪では正解コードを復元し、質問パネルを表示しない", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = typeof input === "string" ? input : input.toString();
      if (url.endsWith("/api/algorithm-quiz/sessions/sess-1")) {
        return mockJsonResponse(completedSession);
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    renderPage();

    expect(await screen.findByText("結果: 二分探索")).toBeInTheDocument();
    expect(screen.getByText("正解コード")).toBeInTheDocument();
    expect(screen.getByText(/def solve\(\):/)).toBeInTheDocument();
    expect(screen.queryByText("問題への質問")).not.toBeInTheDocument();
  });

  it("submit中に別セッションへ遷移しても古い結果で画面を汚さない", async () => {
    const submitDeferred = deferred<Response>();
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = typeof input === "string" ? input : input.toString();
      if (url.endsWith("/api/algorithm-quiz/sessions/sess-1/answer")) {
        return submitDeferred.promise;
      }
      if (url.endsWith("/api/algorithm-quiz/sessions/sess-1")) {
        return Promise.resolve(mockJsonResponse(inProgressSession));
      }
      if (url.endsWith("/api/algorithm-quiz/sessions/sess-2")) {
        return Promise.resolve(
          mockJsonResponse({
            ...inProgressSession,
            session_id: "sess-2",
            theme_id: "algo-002",
            theme_label: "DFS",
            problem_statement: "別の問題文です",
          }),
        );
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    renderPage();

    const codeTextarea = (await screen.findByPlaceholderText(
      "# Python で解答を書いてください",
    )) as HTMLTextAreaElement;
    fireEvent.change(codeTextarea, { target: { value: "print(1)" } });
    fireEvent.click(screen.getByRole("button", { name: "提出" }));
    fireEvent.click(screen.getByRole("button", { name: "go sess-2" }));

    expect(await screen.findByText("別の問題文です")).toBeInTheDocument();

    submitDeferred.resolve(mockJsonResponse(submitResult));

    await waitFor(() => {
      expect(screen.getAllByText("DFS").length).toBeGreaterThan(0);
    });
    expect(screen.queryByText("結果: 二分探索")).not.toBeInTheDocument();
    expect(screen.queryByText("正解コード")).not.toBeInTheDocument();
  });

  it("質問失敗時はドラフトを保持する", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = typeof input === "string" ? input : input.toString();
      if (url.endsWith("/api/algorithm-quiz/sessions/sess-1/question")) {
        return {
          ok: false,
          status: 503,
          text: () => Promise.resolve("temporary failure"),
        } as Response;
      }
      if (url.endsWith("/api/algorithm-quiz/sessions/sess-1")) {
        return mockJsonResponse(inProgressSession);
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    renderPage();

    const chatTextarea = (await screen.findByPlaceholderText(
      "制約の見方、考える順番、計算量の見積もりなどを質問できます",
    )) as HTMLTextAreaElement;
    fireEvent.change(chatTextarea, {
      target: { value: "どこから考えればいい？" },
    });
    fireEvent.click(screen.getByRole("button", { name: "質問する" }));

    await waitFor(() => {
      expect(chatTextarea.value).toBe("どこから考えればいい？");
    });
    expect(screen.queryByText("あなた")).not.toBeInTheDocument();
  });

  it("質問中に別セッションへ遷移しても古い応答を混入させない", async () => {
    const questionDeferred = deferred<Response>();
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = typeof input === "string" ? input : input.toString();
      if (url.endsWith("/api/algorithm-quiz/sessions/sess-1/question")) {
        return questionDeferred.promise;
      }
      if (url.endsWith("/api/algorithm-quiz/sessions/sess-1")) {
        return Promise.resolve(mockJsonResponse(inProgressSession));
      }
      if (url.endsWith("/api/algorithm-quiz/sessions/sess-2")) {
        return Promise.resolve(
          mockJsonResponse({
            ...inProgressSession,
            session_id: "sess-2",
            theme_id: "algo-002",
            theme_label: "DFS",
            problem_statement: "別の問題文です",
          }),
        );
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    renderPage();

    const chatTextarea = (await screen.findByPlaceholderText(
      "制約の見方、考える順番、計算量の見積もりなどを質問できます",
    )) as HTMLTextAreaElement;
    fireEvent.change(chatTextarea, {
      target: { value: "どこから考えればいい？" },
    });
    fireEvent.click(screen.getByRole("button", { name: "質問する" }));
    fireEvent.click(screen.getByRole("button", { name: "go sess-2" }));

    expect(await screen.findByText("別の問題文です")).toBeInTheDocument();

    questionDeferred.resolve(
      mockJsonResponse({
        session_id: "sess-1",
        chat_response_text: "これは sess-1 用のヒントです。",
      }),
    );

    await waitFor(() => {
      expect(screen.getAllByText("DFS").length).toBeGreaterThan(0);
    });
    expect(
      screen.queryByText("これは sess-1 用のヒントです。"),
    ).not.toBeInTheDocument();
  });
});
