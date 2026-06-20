import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { renderWithProviders, mockJsonResponse } from "@/test-utils";
import { SqlDojoPage } from "./sql-dojo-page";

const mockCatalog = {
  difficulties: ["beginner", "intermediate", "advanced"],
  themes: [
    {
      family: "join-basics",
      difficulty: "beginner",
      business_domain: "EC",
      target_skill: "JOIN",
      title: "顧客別注文件数",
      variant_count: 3,
      attempt_count: 0,
      best_score: null,
      last_attempted_at: null,
    },
    {
      family: "window-ranking",
      difficulty: "intermediate",
      business_domain: "HR",
      target_skill: "Window Function",
      title: "部門別ランキング",
      variant_count: 2,
      attempt_count: 0,
      best_score: null,
      last_attempted_at: null,
    },
  ],
};

afterEach(() => {
  vi.restoreAllMocks();
  window.localStorage.clear();
});

describe("SqlDojoPage", () => {
  it("全難易度のテーマと問題数を表示する", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = typeof input === "string" ? input : input.toString();
      if (url.includes("/sql-dojo/catalog")) {
        return mockJsonResponse(mockCatalog);
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    renderWithProviders(<SqlDojoPage />, {
      initialEntries: ["/sql-dojo"],
    });

    expect(await screen.findByText("顧客別注文件数")).toBeInTheDocument();
    expect(screen.getByText("部門別ランキング")).toBeInTheDocument();
    expect(screen.getByText("全 2 テーマ / 5 問")).toBeInTheDocument();
    expect(screen.getByText("3問")).toBeInTheDocument();
    expect(screen.getByText("2問")).toBeInTheDocument();
  });

  it("開始時に選択した難易度を送る", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockImplementation(
      async (input, init) => {
        const url = typeof input === "string" ? input : input.toString();
        if (url.includes("/sql-dojo/catalog")) {
          return mockJsonResponse(mockCatalog);
        }
        if (url.endsWith("/sql-dojo/sessions")) {
          expect(init?.method).toBe("POST");
          expect(init?.body).toBe(JSON.stringify({ difficulty: "intermediate" }));
          return mockJsonResponse({
            session_id: "sql-1",
            theme_family: "window-ranking",
            difficulty: "intermediate",
            dialect: "postgresql",
            theme_title: "部門別ランキング",
            business_domain: "HR",
            target_skill: "Window Function",
            problem_statement: "問題文",
            schema_markdown: "schema",
            sample_data_json: "[]",
            expected_focus: "ROW_NUMBER",
          });
        }
        throw new Error(`Unexpected fetch: ${url}`);
      },
    );

    renderWithProviders(<SqlDojoPage />, {
      initialEntries: ["/sql-dojo"],
    });

    await screen.findByText("顧客別注文件数");
    fireEvent.change(screen.getByLabelText("難易度"), {
      target: { value: "intermediate" },
    });
    fireEvent.click(screen.getByRole("button", { name: "次の1問" }));

    await waitFor(() => {
      expect(fetchSpy).toHaveBeenCalled();
    });
  });

  it("テーマカード開始ではカード側の難易度を送る", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockImplementation(
      async (input, init) => {
        const url = typeof input === "string" ? input : input.toString();
        if (url.includes("/sql-dojo/catalog")) {
          return mockJsonResponse(mockCatalog);
        }
        if (url.endsWith("/sql-dojo/sessions")) {
          expect(init?.method).toBe("POST");
          expect(init?.body).toBe(JSON.stringify({
            difficulty: "intermediate",
            theme_family: "window-ranking",
          }));
          return mockJsonResponse({
            session_id: "sql-2",
            theme_family: "window-ranking",
            difficulty: "intermediate",
            dialect: "postgresql",
            theme_title: "部門別ランキング",
            business_domain: "HR",
            target_skill: "Window Function",
            problem_statement: "問題文",
            schema_markdown: "schema",
            sample_data_json: "[]",
            expected_focus: "ROW_NUMBER",
          });
        }
        throw new Error(`Unexpected fetch: ${url}`);
      },
    );

    renderWithProviders(<SqlDojoPage />, {
      initialEntries: ["/sql-dojo"],
    });

    const themeTitle = await screen.findByText("部門別ランキング");
    const themeCard = themeTitle.closest("div.rounded-lg");
    expect(themeCard).not.toBeNull();
    fireEvent.click(
      within(themeCard as HTMLElement).getByRole("button", {
        name: "このテーマを解く",
      }),
    );

    await waitFor(() => {
      expect(fetchSpy).toHaveBeenCalled();
    });
  });

  it("テーマごとの挑戦回数と最高点を表示する", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = typeof input === "string" ? input : input.toString();
      if (url.includes("/sql-dojo/catalog")) {
        return mockJsonResponse({
          ...mockCatalog,
          themes: [
            {
              ...mockCatalog.themes[0],
              difficulty: "beginner",
              attempt_count: 2,
              best_score: 91,
              last_attempted_at: "2026-06-21T00:00:00+09:00",
            },
            mockCatalog.themes[1],
          ],
        });
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    renderWithProviders(<SqlDojoPage />, {
      initialEntries: ["/sql-dojo"],
    });

    expect(await screen.findByText("顧客別注文件数")).toBeInTheDocument();
    expect(screen.getByText("2 回挑戦")).toBeInTheDocument();
    expect(screen.getByText("最高 91 点")).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "このテーマを解く" }).length).toBeGreaterThan(0);
  });
});
