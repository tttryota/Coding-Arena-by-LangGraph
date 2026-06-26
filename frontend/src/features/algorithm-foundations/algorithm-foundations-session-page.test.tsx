import { fireEvent, screen } from "@testing-library/react";
import { Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { mockJsonResponse, renderWithProviders } from "@/test-utils";
import type {
  AlgorithmFoundationAnswerResponse,
  AlgorithmFoundationSessionResponse,
} from "@/types/api";
import { AlgorithmFoundationsSessionPage } from "./algorithm-foundations-session-page";

const inProgressSession: AlgorithmFoundationSessionResponse = {
  session_id: "af-1",
  unit_id: "algo-102-hashmap-count",
  group_id: "group-0",
  group_title: "データ構造",
  unit_title: "出現回数カウント",
  target_skill: "出現回数カウント",
  unit_kind: "foundation",
  prerequisite_unit_ids: ["algo-102-hashmap-exists"],
  prerequisite_titles: ["存在判定をハッシュで高速化"],
  allowed_knowledge: ["出現回数カウント", "ハッシュマップ・ハッシュセット"],
  forbidden_knowledge: ["尺取り法"],
  problem_id: "p-1",
  problem_title: "出現回数カウント / 典型入力をそのまま処理する",
  programming_language: "python",
  problem_statement:
    "値ごとの出現回数を連想配列にため、あとで必要な回数をすぐ取り出せるようにする考え方です。数え上げを map の更新に置き換える形を身につけます。\n\n問題文です",
  input_format: "入力形式",
  output_format: "出力形式",
  constraints: "制約",
  examples: [{ input: "1", output: "2" }],
  recommended: false,
  has_unmet_prerequisites: true,
  status: "in_progress",
  created_at: "2026-06-25T00:00:00+09:00",
};

const completedSession: AlgorithmFoundationSessionResponse = {
  ...inProgressSession,
  status: "completed",
  score: 88,
  feedback: "よい実装です",
  time_complexity: "O(N)",
  space_complexity: "O(N)",
  improvement_suggestions: "境界条件の確認を加えるとさらに安定します",
  rubric_scores_json: "[]",
  reference_solution: "def solve():\n    return 42",
};

const submitResult: AlgorithmFoundationAnswerResponse = {
  session_id: "af-1",
  score: 91,
  feedback: "よい解答です",
  time_complexity: "O(N)",
  space_complexity: "O(N)",
  improvement_suggestions: "変数名を整理するとさらに読みやすいです",
  rubric_scores_json: "[]",
  reference_solution: "def solve():\n    return 42",
};

function renderPage(sessionId = "af-1") {
  return renderWithProviders(
    <Routes>
      <Route
        path="/algorithm-foundations/:sessionId"
        element={<AlgorithmFoundationsSessionPage />}
      />
    </Routes>,
    {
      initialEntries: [`/algorithm-foundations/${sessionId}`],
    },
  );
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("AlgorithmFoundationsSessionPage", () => {
  it("提出直後に結果と模範解答を表示する", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = typeof input === "string" ? input : input.toString();
      if (url.endsWith("/api/algorithm-foundations/sessions/af-1/answer")) {
        return mockJsonResponse(submitResult);
      }
      if (url.endsWith("/api/algorithm-foundations/sessions/af-1")) {
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

    expect(await screen.findByText("結果: 出現回数カウント")).toBeInTheDocument();
    expect(screen.getByText("模範解答")).toBeInTheDocument();
    expect(screen.getByText(/def solve\(\):/)).toBeInTheDocument();
  });

  it("完了済みセッション再訪時は結果を復元する", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = typeof input === "string" ? input : input.toString();
      if (url.endsWith("/api/algorithm-foundations/sessions/af-1")) {
        return mockJsonResponse(completedSession);
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    renderPage();

    expect(await screen.findByText("結果: 出現回数カウント")).toBeInTheDocument();
    expect(screen.getByText("模範解答")).toBeInTheDocument();
    expect(screen.queryByText("解答コード")).not.toBeInTheDocument();
  });

  it("セッション言語に応じた placeholder を表示する", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = typeof input === "string" ? input : input.toString();
      if (url.endsWith("/api/algorithm-foundations/sessions/af-1")) {
        return mockJsonResponse({
          ...inProgressSession,
          programming_language: "typescript",
        });
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    renderPage();

    expect(
      await screen.findByPlaceholderText("// TypeScript で解答を書いてください"),
    ).toBeInTheDocument();
  });

  it("問題に不要な補助カードを表示しない", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = typeof input === "string" ? input : input.toString();
      if (url.endsWith("/api/algorithm-foundations/sessions/af-1")) {
        return mockJsonResponse(inProgressSession);
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    renderPage();

    await screen.findByText("出現回数カウント / 典型入力をそのまま処理する");

    expect(screen.queryByText("この unit で見るもの")).not.toBeInTheDocument();
    expect(screen.queryByText("この 1 問のルール")).not.toBeInTheDocument();
    expect(screen.queryByText("ターゲットスキル")).not.toBeInTheDocument();
    expect(screen.queryByText("使ってよい知識")).not.toBeInTheDocument();
    expect(screen.queryByText("今回は使わない知識")).not.toBeInTheDocument();
    expect(screen.queryByText("前提 unit")).not.toBeInTheDocument();
  });

  it("問題文の先頭で知識の説明を表示する", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = typeof input === "string" ? input : input.toString();
      if (url.endsWith("/api/algorithm-foundations/sessions/af-1")) {
        return mockJsonResponse(inProgressSession);
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    renderPage();

    expect(
      await screen.findByText(/値ごとの出現回数を連想配列にため/),
    ).toBeInTheDocument();
  });
});
