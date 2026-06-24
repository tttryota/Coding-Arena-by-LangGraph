import { fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders, mockJsonResponse } from "@/test-utils";
import { AlgorithmFoundationsPage } from "./algorithm-foundations-page";

const mockCatalog = {
  total_unit_count: 3,
  total_problem_count: 9,
  groups: [
    {
      group_id: "group-0",
      group_title: "データ構造",
      order: 0,
      units: [
        {
          unit_id: "algo-093-stack-basics",
          theme_id: "algo-093",
          title: "スタックの基本操作",
          display_order: 0,
          prerequisite_unit_ids: [],
          prerequisite_titles: [],
          target_skill: "スタックの基本操作",
          unit_kind: "foundation",
          problem_count: 3,
          best_score: null,
          last_attempted_at: null,
          recommended: true,
          has_unmet_prerequisites: false,
        },
        {
          unit_id: "algo-102-hashmap-count",
          theme_id: "algo-102",
          title: "出現回数カウント",
          display_order: 1,
          prerequisite_unit_ids: ["algo-102-hashmap-exists"],
          prerequisite_titles: ["存在判定をハッシュで高速化"],
          target_skill: "出現回数カウント",
          unit_kind: "foundation",
          problem_count: 3,
          best_score: 81,
          last_attempted_at: "2026-06-25T10:00:00+09:00",
          recommended: false,
          has_unmet_prerequisites: true,
        },
      ],
    },
    {
      group_id: "group-1",
      group_title: "探索",
      order: 1,
      units: [
        {
          unit_id: "algo-004-dfs-trace",
          theme_id: "algo-004",
          title: "DFSの辿り順を追う",
          display_order: 2,
          prerequisite_unit_ids: ["algo-004-basic", "algo-004-stack-model"],
          prerequisite_titles: ["深さ優先探索の基本", "再帰とスタックの対応"],
          target_skill: "探索順を手で追って検証する",
          unit_kind: "foundation",
          problem_count: 4,
          best_score: null,
          last_attempted_at: null,
          recommended: false,
          has_unmet_prerequisites: true,
        },
      ],
    },
  ],
};

const mockSessions = {
  sessions: [
    {
      session_id: "af-1",
      unit_id: "algo-102-hashmap-count",
      group_id: "group-0",
      group_title: "データ構造",
      unit_title: "出現回数カウント",
      target_skill: "出現回数カウント",
      unit_kind: "foundation",
      problem_id: "p-1",
      problem_title: "問題1",
      programming_language: "python",
      status: "completed",
      created_at: "2026-06-25T10:00:00+09:00",
      score: 81,
    },
  ],
};

afterEach(() => {
  vi.restoreAllMocks();
});

function mockFetch() {
  return vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
    const url = typeof input === "string" ? input : input.toString();
    if (url.includes("/algorithm-foundations/catalog")) {
      return mockJsonResponse(mockCatalog);
    }
    if (url.includes("/algorithm-foundations/sessions")) {
      if (init?.method === "POST") {
        return mockJsonResponse({
          session_id: "sess-1",
          unit_id: "algo-102-hashmap-count",
          group_id: "group-0",
          group_title: "データ構造",
          unit_title: "出現回数カウント",
          target_skill: "出現回数カウント",
          unit_kind: "foundation",
          problem_id: "p-1",
          problem_title: "問題1",
          programming_language: "python",
          problem_statement: "問題文",
          input_format: "入力",
          output_format: "出力",
          constraints: "制約",
          examples: [],
          prerequisite_unit_ids: ["algo-102-hashmap-exists"],
          prerequisite_titles: ["存在判定をハッシュで高速化"],
          allowed_knowledge: ["出現回数カウント", "ハッシュマップ・ハッシュセット"],
          forbidden_knowledge: ["尺取り法"],
          recommended: false,
          has_unmet_prerequisites: true,
        });
      }
      return mockJsonResponse(mockSessions);
    }
    throw new Error(`Unexpected fetch: ${url}`);
  });
}

describe("AlgorithmFoundationsPage", () => {
  it("推奨unitと前提警告を表示する", async () => {
    mockFetch();

    renderWithProviders(<AlgorithmFoundationsPage />, {
      initialEntries: ["/algorithm-foundations"],
    });

    expect(
      await screen.findByRole("heading", { name: "競プロうさぎ" }),
    ).toBeInTheDocument();
    expect(screen.getByText("目次")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /データ構造/ })).toHaveAttribute(
      "href",
      "#foundation-group-group-0",
    );
    expect(screen.getByRole("link", { name: /探索/ })).toHaveAttribute(
      "href",
      "#foundation-group-group-1",
    );
    expect(screen.getByText("次: スタックの基本操作")).toBeInTheDocument();
    expect(screen.getAllByText("出現回数カウント").length).toBeGreaterThan(0);
    expect(screen.getAllByText("前提注意")).toHaveLength(2);
    expect(screen.getByText("前提: 存在判定をハッシュで高速化")).toBeInTheDocument();
    expect(
      screen.getByText("前提: 深さ優先探索の基本 / 再帰とスタックの対応"),
    ).toBeInTheDocument();
  });

  it("unit指定で開始リクエストを送る", async () => {
    const fetchSpy = mockFetch();

    renderWithProviders(<AlgorithmFoundationsPage />, {
      initialEntries: ["/algorithm-foundations"],
    });

    expect(
      await screen.findByRole("heading", { name: "競プロうさぎ" }),
    ).toBeInTheDocument();
    fireEvent.click(screen.getAllByRole("button", { name: "解く" })[1]);

    await waitFor(() => {
      expect(fetchSpy).toHaveBeenCalled();
    });
    const startCall = fetchSpy.mock.calls.find(([, init]) => init?.method === "POST");
    expect(startCall).toBeDefined();
    expect(JSON.parse(String(startCall?.[1]?.body))).toEqual({
      unit_id: "algo-102-hashmap-count",
    });
  });
});
