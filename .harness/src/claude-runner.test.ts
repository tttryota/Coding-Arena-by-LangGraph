import test from "node:test";
import assert from "node:assert/strict";
import { extractClaudeText } from "./claude-runner.ts";

test("extractClaudeText prefers structured output when text result is empty", () => {
  const text = extractClaudeText({
    result: "",
    structured_output: { ok: true, route: "claudeOpusReview" },
    session_id: "session",
    is_error: false,
    total_cost_usd: 0,
    usage: {
      input_tokens: 1,
      output_tokens: 1,
    },
  });

  assert.equal(text, JSON.stringify({ ok: true, route: "claudeOpusReview" }));
});
