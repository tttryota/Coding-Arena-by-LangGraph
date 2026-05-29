import { screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { renderWithProviders, mockJsonResponse } from "@/test-utils";
import { CompetitivePage } from "./competitive-page";

const mockThemes = {
  themes: [
    { id: "algo-001", category: "探索", label: "二分探索" },
    { id: "algo-002", category: "グラフ", label: "ダイクストラ法" },
  ],
};

afterEach(() => {
  vi.restoreAllMocks();
});

describe("CompetitivePage", () => {
  it("テーマ一覧を表示する", async () => {
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(mockJsonResponse(mockThemes));

    renderWithProviders(<CompetitivePage />, {
      initialEntries: ["/algorithm-quiz"],
    });

    await waitFor(() => {
      expect(screen.getByText("二分探索")).toBeInTheDocument();
    });
    expect(screen.getByText("ダイクストラ法")).toBeInTheDocument();
    expect(fetchSpy).toHaveBeenCalled();
  });

  it("ランダムで挑戦ボタンが表示される", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      mockJsonResponse(mockThemes),
    );

    renderWithProviders(<CompetitivePage />, {
      initialEntries: ["/algorithm-quiz"],
    });

    await waitFor(() => {
      expect(screen.getByText("ランダムで挑戦")).toBeInTheDocument();
    });
  });
});
