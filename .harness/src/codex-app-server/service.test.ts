import test from "node:test";
import assert from "node:assert/strict";
import { CodexConversationService } from "./service.ts";
import type { AppServerTransport } from "./transport.ts";
import type { JsonRpcNotification } from "./protocol.ts";
import type { RunnerRequest, RunnerReviewRequest } from "../runner.ts";

class FakeTransport implements AppServerTransport {
  requests: Array<{ method: string; params: unknown }> = [];
  private listeners = new Set<(notification: JsonRpcNotification) => void>();

  subscribe(listener: (notification: JsonRpcNotification) => void): () => void {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  async request(method: string, params: unknown): Promise<unknown> {
    this.requests.push({ method, params });

    if (method === "initialize") {
      return { userAgent: "codex", codexHome: "/tmp/codex", platformFamily: "unix", platformOs: "macos" };
    }

    if (method === "thread/start") {
      return { thread: { id: "thread-1" } };
    }

    if (method === "thread/resume") {
      return { thread: { id: "thread-1" } };
    }

    if (method === "turn/start") {
      setTimeout(() => {
        this.emit({
          jsonrpc: "2.0",
          method: "item/completed",
          params: {
            threadId: "thread-1",
            turnId: "turn-1",
            item: {
              type: "agentMessage",
              id: "msg-1",
              text: "{\"issues\":[]}",
              phase: "final_answer",
            },
          },
        });
        this.emit({
          jsonrpc: "2.0",
          method: "thread/tokenUsage/updated",
          params: {
            threadId: "thread-1",
            turnId: "turn-1",
            tokenUsage: {
              total: {
                totalTokens: 18,
                inputTokens: 10,
                cachedInputTokens: 3,
                outputTokens: 5,
                reasoningOutputTokens: 0,
              },
              last: {
                totalTokens: 18,
                inputTokens: 10,
                cachedInputTokens: 3,
                outputTokens: 5,
                reasoningOutputTokens: 0,
              },
            },
          },
        });
        this.emit({
          jsonrpc: "2.0",
          method: "turn/completed",
          params: {
            threadId: "thread-1",
            turn: {
              id: "turn-1",
              status: "completed",
              error: null,
            },
          },
        });
      }, 0);

      return { turn: { id: "turn-1", status: "running", error: null } };
    }

    if (method === "review/start") {
      setTimeout(() => {
        this.emit({
          jsonrpc: "2.0",
          method: "item/completed",
          params: {
            threadId: "review-thread-1",
            turnId: "review-turn-1",
            item: {
              type: "exitedReviewMode",
              id: "review-1",
              review: "{\"issues\":[]}",
            },
          },
        });
        this.emit({
          jsonrpc: "2.0",
          method: "turn/completed",
          params: {
            threadId: "review-thread-1",
            turn: {
              id: "review-turn-1",
              status: "completed",
              error: null,
            },
          },
        });
      }, 0);

      return {
        turn: { id: "review-turn-1", status: "running", error: null },
        reviewThreadId: "review-thread-1",
      };
    }

    throw new Error(`unexpected method ${method}`);
  }

  async close(): Promise<void> {}

  private emit(notification: JsonRpcNotification): void {
    for (const listener of this.listeners) {
      listener(notification);
    }
  }
}

test("CodexConversationService starts a thread and completes a turn", async () => {
  const transport = new FakeTransport();
  const service = new CodexConversationService(transport);
  const request: RunnerRequest = {
    prompt: "review this",
    cwd: "/repo",
    timeoutMs: 1000,
    sandboxPolicy: "workspace-write",
    approvalPolicy: "never",
    outputSchema: { type: "object" },
  };

  const response = await service.runTurn(request, {
    cwd: "/repo",
    sandbox: "workspace-write",
    approvalPolicy: "never",
  });

  assert.equal(response.text, "{\"issues\":[]}");
  assert.equal(response.sessionId, "thread-1");
  assert.deepEqual(
    transport.requests.map((entry) => entry.method),
    ["initialize", "thread/start", "turn/start"],
  );
  assert.equal(response.metadata?.inputTokens, 13);
  assert.equal(response.metadata?.outputTokens, 5);
  assert.equal(response.metadata?.cacheReadInputTokens, 3);
});

test("CodexConversationService uses detached review threads", async () => {
  const transport = new FakeTransport();
  const service = new CodexConversationService(transport);
  const request: RunnerReviewRequest = {
    sessionId: "thread-1",
    cwd: "/repo",
    timeoutMs: 1000,
    instructions: "review these files",
    delivery: "detached",
  };

  const response = await service.runReview(request, {
    cwd: "/repo",
    sandbox: "read-only",
    approvalPolicy: "never",
  });

  assert.equal(response.text, "{\"issues\":[]}");
  assert.equal(response.sessionId, "review-thread-1");
  assert.deepEqual(
    transport.requests.map((entry) => entry.method),
    ["initialize", "thread/resume", "review/start"],
  );
});
