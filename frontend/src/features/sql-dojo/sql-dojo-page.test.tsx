import { fireEvent, screen, waitFor } from "@testing-library/react";
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
    },
    {
      family: "window-ranking",
      difficulty: "intermediate",
      business_domain: "HR",
      target_skill: "Window Function",
      title: "部門別ランキング",
    },
  ],
};

afterEach(() => {
  vi.restoreAllMocks();
  window.localStorage.clear();
});

describe("SqlDojoPage", () => {
  it("難易度別のテーマを表示する", async () => {
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
    fireEvent.change(screen.getByLabelText("難易度"), {
      target: { value: "intermediate" },
    });
    expect(await screen.findByText("部門別ランキング")).toBeInTheDocument();
  });

  it("開始時に選択した難易度を送る", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockImplementation(
      async (input, init) => {
        const url = typeof input === "string" ? input : input.toString();
        if (url.includes("/sql-dojo/catalog")) {
          return mockJsonResponse(mockCatalog);
        }
        if (url.includes("/sql-dojo/sessions")) {
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
});
