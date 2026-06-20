import { fireEvent, screen, waitFor } from "@testing-library/react";
import { Route, Routes, useNavigate } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { SqlDojoSessionPage } from "./sql-dojo-session-page";
import { useSqlDojoStore } from "./use-sql-dojo-store";
import { mockJsonResponse, renderWithProviders } from "@/test-utils";
import type {
  SqlDojoAnswerResponse,
  SqlDojoSessionResponse,
} from "@/types/api";

const inProgressSession: SqlDojoSessionResponse = {
  session_id: "sql-1",
  theme_family: "join-basics",
  topic_id: "join-basics-shipped-orders",
  topic_title: "shipped注文件数",
  difficulty: "beginner",
  dialect: "postgresql",
  theme_title: "顧客別注文件数",
  business_domain: "EC",
  target_skill: "JOIN",
  problem_statement: "問題文です",
  schema_markdown: "```sql\ncustomers(...)\n```",
  sample_data_json: '[{"table":"customers","rows":100}]',
  expected_focus: "JOIN, COUNT",
  status: "in_progress",
  created_at: "2026-06-19T00:00:00+09:00",
};

const completedSession: SqlDojoSessionResponse = {
  ...inProgressSession,
  status: "completed",
  score: 84,
  feedback: "良い観点です",
  rule_breakdown_json: "[]",
  improvement_suggestions: "JOIN 条件を確認してください",
  reference_sql: "SELECT 1",
};

const submitResult: SqlDojoAnswerResponse = {
  session_id: "sql-1",
  score: 92,
  feedback: "良い解答です",
  rule_breakdown_json: "[]",
  improvement_suggestions: "ORDER BY を明示できています",
  reference_sql: "SELECT 1",
};

function SessionNavigator() {
  const navigate = useNavigate();
  return (
    <>
      <button type="button" onClick={() => navigate("/sql-dojo/sql-1")}>
        go sql-1
      </button>
      <button type="button" onClick={() => navigate("/sql-dojo/sql-2")}>
        go sql-2
      </button>
      <Routes>
        <Route path="/sql-dojo/:sessionId" element={<SqlDojoSessionPage />} />
      </Routes>
    </>
  );
}

function renderPage(sessionId = "sql-1") {
  return renderWithProviders(<SessionNavigator />, {
    initialEntries: [`/sql-dojo/${sessionId}`],
  });
}

afterEach(() => {
  vi.restoreAllMocks();
});

beforeEach(() => {
  useSqlDojoStore.getState().reset();
});

describe("SqlDojoSessionPage", () => {
  it("質問送信ができる", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = typeof input === "string" ? input : input.toString();
      if (url.endsWith("/api/sql-dojo/sessions/sql-1/question")) {
        expect(init?.method).toBe("POST");
        return mockJsonResponse({
          session_id: "sql-1",
          chat_response_text: "まず必要なテーブルと集約を分けて考えてください。",
        });
      }
      if (url.endsWith("/api/sql-dojo/sessions/sql-1")) {
        return mockJsonResponse(inProgressSession);
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    renderPage();

    expect(await screen.findByText("問題文です")).toBeInTheDocument();
    const chatTextarea = screen.getByLabelText(
      "ヒントを質問",
    ) as HTMLTextAreaElement;
    fireEvent.change(chatTextarea, {
      target: { value: "どこから考える？" },
    });
    fireEvent.click(screen.getByRole("button", { name: "質問する" }));

    await waitFor(() => {
      expect(
        screen.getByText("まず必要なテーブルと集約を分けて考えてください。"),
      ).toBeInTheDocument();
    });
    expect(chatTextarea.value).toBe("");
  });

  it("提出後は結果と参考 SQL を表示する", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = typeof input === "string" ? input : input.toString();
      if (url.endsWith("/api/sql-dojo/sessions/sql-1/answer")) {
        return mockJsonResponse(submitResult);
      }
      if (url.endsWith("/api/sql-dojo/sessions/sql-1")) {
        return mockJsonResponse(inProgressSession);
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    renderPage();

    const sqlTextarea = (await screen.findByLabelText(
      "SQL を入力",
    )) as HTMLTextAreaElement;
    fireEvent.change(sqlTextarea, { target: { value: "SELECT 1" } });
    fireEvent.click(screen.getByRole("button", { name: "提出" }));

    expect(await screen.findByText("結果: shipped注文件数")).toBeInTheDocument();
    expect(screen.getByText("参考 SQL")).toBeInTheDocument();
    expect(screen.getByText(/SELECT 1/)).toBeInTheDocument();
  });

  it("SQL 入力欄では Tab キーでタブ文字を挿入する", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = typeof input === "string" ? input : input.toString();
      if (url.endsWith("/api/sql-dojo/sessions/sql-1")) {
        return mockJsonResponse(inProgressSession);
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    renderPage();

    const sqlTextarea = (await screen.findByLabelText(
      "SQL を入力",
    )) as HTMLTextAreaElement;
    fireEvent.change(sqlTextarea, { target: { value: "SELECT\nFROM users" } });
    sqlTextarea.selectionStart = 7;
    sqlTextarea.selectionEnd = 7;

    fireEvent.keyDown(sqlTextarea, { key: "Tab" });

    await waitFor(() => {
      expect(sqlTextarea.value).toBe("SELECT\n\tFROM users");
    });
  });

  it("完了済みセッション再訪では結果と参考 SQL を表示する", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = typeof input === "string" ? input : input.toString();
      if (url.endsWith("/api/sql-dojo/sessions/sql-1")) {
        return mockJsonResponse(completedSession);
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    renderPage();

    expect(await screen.findByText("結果: shipped注文件数")).toBeInTheDocument();
    expect(screen.getByText("参考 SQL")).toBeInTheDocument();
    expect(screen.getByText(/SELECT 1/)).toBeInTheDocument();
    expect(screen.queryByText("問題への質問")).not.toBeInTheDocument();
  });

  it("結果表示のコードブロックは横スクロール可能", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = typeof input === "string" ? input : input.toString();
      if (url.endsWith("/api/sql-dojo/sessions/sql-1")) {
        return mockJsonResponse(completedSession);
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    renderPage();

    await screen.findByText("結果: shipped注文件数");
    const sqlBlock = screen.getByText(/SELECT 1/).closest("div");
    expect(sqlBlock?.className).toContain("overflow-x-auto");
  });
});
