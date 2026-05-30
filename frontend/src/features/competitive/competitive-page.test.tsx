import { screen, waitFor } from "@testing-library/react";
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
  return vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
    const url = typeof input === "string" ? input : input.toString();
    if (url.includes("/algorithm-quiz/themes")) {
      return mockJsonResponse(themes);
    }
    if (url.includes("/algorithm-quiz/sessions")) {
      return mockJsonResponse(sessions);
    }
    throw new Error(`Unexpected fetch: ${url}`);
  });
}

afterEach(() => {
  vi.restoreAllMocks();
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
});
