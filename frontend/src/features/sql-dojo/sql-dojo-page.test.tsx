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
      topics: [
        {
          topic_id: "join-basics-shipped-orders",
          topic_title: "shipped注文件数",
          family: "join-basics",
          difficulty: "beginner",
          business_domain: "EC",
          target_skill: "JOIN",
          attempt_count: 0,
          best_score: null,
          last_attempted_at: null,
        },
        {
          topic_id: "join-basics-open-tickets",
          topic_title: "未解決チケット数",
          family: "join-basics",
          difficulty: "beginner",
          business_domain: "EC",
          target_skill: "JOIN",
          attempt_count: 0,
          best_score: null,
          last_attempted_at: null,
        },
        {
          topic_id: "join-basics-course-completions",
          topic_title: "講座完了件数",
          family: "join-basics",
          difficulty: "beginner",
          business_domain: "EC",
          target_skill: "JOIN",
          attempt_count: 0,
          best_score: null,
          last_attempted_at: null,
        },
      ],
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
      topics: [
        {
          topic_id: "window-ranking-department-sales",
          topic_title: "department別売上1位",
          family: "window-ranking",
          difficulty: "intermediate",
          business_domain: "HR",
          target_skill: "Window Function",
          attempt_count: 0,
          best_score: null,
          last_attempted_at: null,
        },
        {
          topic_id: "window-ranking-service-deployments",
          topic_title: "service別最新成功deploy",
          family: "window-ranking",
          difficulty: "intermediate",
          business_domain: "HR",
          target_skill: "Window Function",
          attempt_count: 0,
          best_score: null,
          last_attempted_at: null,
        },
      ],
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
    expect(screen.getByText("shipped注文件数")).toBeInTheDocument();
    expect(screen.getByText("department別売上1位")).toBeInTheDocument();
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
            topic_id: "window-ranking-department-sales",
            topic_title: "department別売上1位",
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

  it("トピック開始では topic_id とトピック側の難易度を送る", async () => {
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
            topic_id: "window-ranking-department-sales",
          }));
          return mockJsonResponse({
            session_id: "sql-2",
            theme_family: "window-ranking",
            topic_id: "window-ranking-department-sales",
            topic_title: "department別売上1位",
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

    const topicTitle = await screen.findByText("department別売上1位");
    const topicRow = topicTitle.closest("div.rounded-md");
    expect(topicRow).not.toBeNull();
    fireEvent.click(
      within(topicRow as HTMLElement).getByRole("button", {
        name: "department別売上1位を解く",
      }),
    );

    await waitFor(() => {
      expect(fetchSpy).toHaveBeenCalled();
    });
  });

  it("トピックごとの挑戦回数と最高点を表示する", async () => {
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
              topics: [
                {
                  ...mockCatalog.themes[0].topics[0],
                  attempt_count: 2,
                  best_score: 91,
                  last_attempted_at: "2026-06-21T00:00:00+09:00",
                },
                mockCatalog.themes[0].topics[1],
                mockCatalog.themes[0].topics[2],
              ],
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

    expect(await screen.findByText("shipped注文件数")).toBeInTheDocument();
    expect(screen.getByText("2 回挑戦")).toBeInTheDocument();
    expect(screen.getByText("最高 91 点")).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: /を解く/ }).length).toBeGreaterThan(0);
  });
});
