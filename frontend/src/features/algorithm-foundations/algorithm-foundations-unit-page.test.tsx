import { fireEvent, screen, waitFor } from "@testing-library/react";
import { Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { mockJsonResponse, renderWithProviders } from "@/test-utils";
import { AlgorithmFoundationsUnitPage } from "./algorithm-foundations-unit-page";

const mockUnitDetail = {
  unit_id: "algo-102-hashmap-count",
  theme_id: "algo-102",
  group_id: "group-0",
  group_title: "データ構造",
  title: "出現回数カウント",
  concept_overview:
    "値ごとの出現回数を連想配列にため、あとで必要な回数をすぐ取り出せるようにする考え方です。数え上げを map の更新に置き換える形を身につけます。",
  display_order: 1,
  prerequisite_unit_ids: ["algo-102-hashmap-exists"],
  prerequisite_titles: ["存在判定をハッシュで高速化"],
  allowed_knowledge: ["出現回数カウント", "ハッシュマップ・ハッシュセット"],
  forbidden_knowledge: ["尺取り法"],
  target_skill: "出現回数カウント",
  unit_kind: "foundation",
  problem_count: 3,
  best_score: 88,
  last_attempted_at: "2026-06-25T10:00:00+09:00",
  has_unmet_prerequisites: true,
  problems: [
    {
      problem_id: "algo-102-hashmap-count-p1",
      title: "出現回数カウント / 基本確認",
      best_score: 88,
      last_attempted_at: "2026-06-25T10:00:00+09:00",
    },
    {
      problem_id: "algo-102-hashmap-count-p2",
      title: "出現回数カウント / 実装確認",
      best_score: null,
      last_attempted_at: null,
    },
  ],
};

afterEach(() => {
  vi.restoreAllMocks();
});

describe("AlgorithmFoundationsUnitPage", () => {
  it("unit detail と problem 一覧を表示する", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = typeof input === "string" ? input : input.toString();
      if (url.endsWith("/api/algorithm-foundations/languages")) {
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
      if (url.endsWith("/api/algorithm-foundations/units/algo-102-hashmap-count")) {
        return mockJsonResponse(mockUnitDetail);
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    renderWithProviders(
      <Routes>
        <Route
          path="/algorithm-foundations/units/:unitId"
          element={<AlgorithmFoundationsUnitPage />}
        />
      </Routes>,
      {
        initialEntries: ["/algorithm-foundations/units/algo-102-hashmap-count"],
      },
    );

    expect(
      await screen.findByRole("heading", { name: "出現回数カウント" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/値ごとの出現回数を連想配列にため/)).toBeInTheDocument();
    expect(screen.getByLabelText("出題言語")).toHaveValue("python");
    expect(screen.getByText("問題一覧")).toBeInTheDocument();
    expect(screen.getByText("出現回数カウント / 基本確認")).toBeInTheDocument();
    expect(screen.getAllByText("最高 88 点")).toHaveLength(2);
    expect(screen.getByText("-")).toBeInTheDocument();
  });

  it("problem を選ぶと unit_id と problem_id を送って開始する", async () => {
    window.localStorage.setItem("competitive-programming-language", "typescript");
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockImplementation(async (input) => {
        const url = typeof input === "string" ? input : input.toString();
        if (url.endsWith("/api/algorithm-foundations/languages")) {
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
        if (url.endsWith("/api/algorithm-foundations/units/algo-102-hashmap-count")) {
          return mockJsonResponse(mockUnitDetail);
        }
        if (url.endsWith("/api/algorithm-foundations/sessions")) {
          return mockJsonResponse({
            session_id: "af-session-1",
            unit_id: "algo-102-hashmap-count",
            group_id: "group-0",
            group_title: "データ構造",
            unit_title: "出現回数カウント",
            target_skill: "出現回数カウント",
            unit_kind: "foundation",
            prerequisite_unit_ids: ["algo-102-hashmap-exists"],
            prerequisite_titles: ["存在判定をハッシュで高速化"],
            allowed_knowledge: ["出現回数カウント"],
            forbidden_knowledge: ["尺取り法"],
            problem_id: "algo-102-hashmap-count-p2",
            problem_title: "出現回数カウント / 実装確認",
            programming_language: "python",
            problem_statement: "問題文",
            input_format: "入力",
            output_format: "出力",
            constraints: "制約",
            examples: [],
            recommended: false,
            has_unmet_prerequisites: true,
          });
        }
        throw new Error(`Unexpected fetch: ${url}`);
      });

    renderWithProviders(
      <Routes>
        <Route
          path="/algorithm-foundations/units/:unitId"
          element={<AlgorithmFoundationsUnitPage />}
        />
        <Route
          path="/algorithm-foundations/:sessionId"
          element={<div>session route</div>}
        />
      </Routes>,
      {
        initialEntries: ["/algorithm-foundations/units/algo-102-hashmap-count"],
      },
    );

    expect(
      await screen.findByRole("heading", { name: "出現回数カウント" }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("出題言語")).toHaveValue("typescript");
    fireEvent.click(screen.getAllByRole("button", { name: "この問題を解く" })[1]);

    await waitFor(() => {
      const startCall = fetchSpy.mock.calls.find(([, init]) => init?.method === "POST");
      expect(startCall).toBeDefined();
      expect(JSON.parse(String(startCall?.[1]?.body))).toEqual({
        unit_id: "algo-102-hashmap-count",
        problem_id: "algo-102-hashmap-count-p2",
        programming_language: "typescript",
      });
    });
    expect(await screen.findByText("session route")).toBeInTheDocument();
  });
});
