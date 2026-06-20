import { fireEvent, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { renderWithProviders, mockJsonResponse } from "@/test-utils";
import { CompetitivePage } from "./competitive-page";

const mockThemes = {
  themes: [
    { id: "algo-001", category: "データ構造", label: "スタック", display_order: 0, attempt_count: 0, best_score: null, last_attempted_at: null },
    { id: "algo-002", category: "探索", label: "二分探索", display_order: 13, attempt_count: 1, best_score: 85, last_attempted_at: "2026-05-29T12:00:00" },
    { id: "algo-003", category: "動的計画法", label: "ナップサック問題", display_order: 30, attempt_count: 0, best_score: null, last_attempted_at: null },
  ],
};

const mockSessions = { sessions: [] };

function mockFetch(themes = mockThemes, sessions = mockSessions) {
  return vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
    const url = typeof input === "string" ? input : input.toString();
    if (url.includes("/algorithm-quiz/languages")) {
      return mockJsonResponse({
        languages: [
          {
            id: "python",
            label: "Python",
            editor_placeholder: "# Python で解答を書いてください",
            enabled_order: 0,
          },
          {
            id: "typescript",
            label: "TypeScript",
            editor_placeholder: "// TypeScript で解答を書いてください",
            enabled_order: 1,
          },
        ],
      });
    }
    if (url.includes("/algorithm-quiz/themes")) {
      return mockJsonResponse(themes);
    }
    if (url.includes("/algorithm-quiz/sessions")) {
      if (init?.method === "POST") {
        return mockJsonResponse({
          session_id: "sess-1",
          theme_id: "algo-001",
          theme_label: "スタック",
          theme_category: "データ構造",
          programming_language: "typescript",
          problem_statement: "問題文",
          input_format: "入力",
          output_format: "出力",
          constraints: "制約",
          examples: [],
        });
      }
      return mockJsonResponse(sessions);
    }
    throw new Error(`Unexpected fetch: ${url}`);
  });
}

afterEach(() => {
  vi.restoreAllMocks();
  window.localStorage.clear();
});

describe("CompetitivePage", () => {
  it("Phase別にテーマを表示する", async () => {
    const fetchSpy = mockFetch();

    renderWithProviders(<CompetitivePage />, {
      initialEntries: ["/algorithm-quiz"],
    });

    await waitFor(() => {
      expect(screen.getByText("スタック")).toBeInTheDocument();
    });
    // Phase見出しが表示される
    expect(screen.getByText("基礎")).toBeInTheDocument();
    expect(screen.getByText("基本")).toBeInTheDocument();
    expect(screen.getByText("二分探索")).toBeInTheDocument();
    expect(screen.getByText("ナップサック問題")).toBeInTheDocument();
    expect(fetchSpy).toHaveBeenCalled();
  });

  it("次のテーマ名がボタンに表示される", async () => {
    mockFetch();

    renderWithProviders(<CompetitivePage />, {
      initialEntries: ["/algorithm-quiz"],
    });

    await waitFor(() => {
      expect(screen.getByText("次: スタック")).toBeInTheDocument();
    });
  });

  it("挑戦済みテーマにスコアが表示される", async () => {
    mockFetch();

    renderWithProviders(<CompetitivePage />, {
      initialEntries: ["/algorithm-quiz"],
    });

    await waitFor(() => {
      expect(screen.getByText("二分探索")).toBeInTheDocument();
    });
    expect(screen.getByText("85")).toBeInTheDocument();
  });

  it("選択した言語で開始リクエストを送る", async () => {
    const fetchSpy = mockFetch();

    renderWithProviders(<CompetitivePage />, {
      initialEntries: ["/algorithm-quiz"],
    });

    await screen.findByText("スタック");
    fireEvent.change(screen.getByLabelText("出題言語"), {
      target: { value: "typescript" },
    });
    fireEvent.click(screen.getByRole("button", { name: "次: スタック" }));

    await waitFor(() => {
      expect(fetchSpy).toHaveBeenCalled();
    });
    const startCall = fetchSpy.mock.calls.find(([, init]) => init?.method === "POST");
    expect(startCall).toBeDefined();
    expect(JSON.parse(String(startCall?.[1]?.body))).toEqual({
      theme_id: undefined,
      programming_language: "typescript",
    });
  });

  it("言語一覧取得失敗時は開始を無効化する", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = typeof input === "string" ? input : input.toString();
      if (url.includes("/algorithm-quiz/languages")) {
        throw new Error("language fetch failed");
      }
      if (url.includes("/algorithm-quiz/themes")) {
        return mockJsonResponse(mockThemes);
      }
      if (url.includes("/algorithm-quiz/sessions")) {
        return mockJsonResponse(mockSessions);
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    renderWithProviders(<CompetitivePage />, {
      initialEntries: ["/algorithm-quiz"],
    });

    expect(await screen.findByText("スタック")).toBeInTheDocument();
    expect(
      screen.getByText("出題言語の取得に失敗したため開始できません。"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "次: スタック" }),
    ).toBeDisabled();
  });

  it("不正な保存済み言語は先頭の言語へ矯正する", async () => {
    window.localStorage.setItem("competitive-programming-language", "ruby");
    mockFetch();

    renderWithProviders(<CompetitivePage />, {
      initialEntries: ["/algorithm-quiz"],
    });

    await waitFor(() => {
      expect(screen.getByLabelText("出題言語")).toHaveValue("python");
    });
    expect(window.localStorage.getItem("competitive-programming-language")).toBe(
      "python",
    );
  });
});
