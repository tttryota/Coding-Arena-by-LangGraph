import { Codex } from "@openai/codex-sdk";
import type { ApprovalMode, Input, SandboxMode, Thread, ThreadEvent, ThreadItem } from "@openai/codex-sdk";
import type { ExecutionCapability, ExecutionRequest, ExecutionResult, ExecutionService } from "./runner.ts";
import { EXECUTION_CAPABILITY } from "./runner.ts";
import type { HarnessLogger } from "./logger.ts";
import { EVENT, HarnessError, RunnerRateLimitError } from "./types.ts";

export const CODEX_SUPPORTED_CAPABILITIES = new Set<ExecutionCapability>([
  EXECUTION_CAPABILITY.SESSION_RESUME,
]);

const DEFAULT_HEARTBEAT_MS = 15_000;
const DEFAULT_STALL_TIMEOUT_MS = 180_000;

type TurnObservability = NonNullable<ExecutionRequest["observability"]>;

type TurnObservationState = {
  firstCommand: string | null;
  firstCommandElapsedMs: number | null;
  firstFileChangeElapsedMs: number | null;
  firstFileChangePaths: string[];
  primaryTargetFileTouched: boolean;
  primaryTargetFileTouchedElapsedMs: number | null;
  nonTargetFileChangeObserved: boolean;
  preTargetExplorationObserved: boolean;
  preTargetCommandSummaries: string[];
};

function toApprovalPolicy(sandbox: string | undefined): ApprovalMode {
  if (sandbox === "danger-full-access" || sandbox === "workspace-write") {
    return "never";
  }
  return "untrusted";
}

function toSandboxMode(sandbox: string | undefined): SandboxMode {
  if (sandbox === "workspace-write" || sandbox === "danger-full-access" || sandbox === "read-only") {
    return sandbox;
  }
  return "workspace-write";
}

export function createCodexExecutionService(defaults?: {
  name?: string;
  timeoutMs?: number;
  sandbox?: string;
  projectRoot?: string;
  heartbeatMs?: number;
  stallTimeoutMs?: number;
}): ExecutionService {
  const codex = new Codex();

  return {
    name: defaults?.name ?? "codex",
    capabilities: CODEX_SUPPORTED_CAPABILITIES,
    async execute(request, logger) {
      if (request.appendSystemPrompt || request.allowedTools || request.agent || request.mcpConfigs) {
        throw new HarnessError("codex transport received unsupported normalized fields.");
      }

      const cwd = request.cwd ?? defaults?.projectRoot;
      const timeoutMs = request.timeoutMs ?? defaults?.timeoutMs;
      const sandboxMode = toSandboxMode(defaults?.sandbox);
      const approvalPolicy = toApprovalPolicy(defaults?.sandbox);
      const thread = request.sessionId
        ? codex.resumeThread(request.sessionId, {
            sandboxMode,
            workingDirectory: cwd,
            skipGitRepoCheck: true,
            approvalPolicy,
          })
        : codex.startThread({
            sandboxMode,
            workingDirectory: cwd,
            skipGitRepoCheck: true,
            approvalPolicy,
          });

      try {
        return await runThread(
          thread,
          request.prompt,
          {
            runnerName: defaults?.name ?? "codex",
            timeoutMs,
            heartbeatMs: defaults?.heartbeatMs ?? DEFAULT_HEARTBEAT_MS,
            stallTimeoutMs: defaults?.stallTimeoutMs ?? DEFAULT_STALL_TIMEOUT_MS,
            observability: request.observability,
          },
          logger,
        );
      } catch (error: unknown) {
        const message = error instanceof Error ? error.message : String(error);
        if (/rate|limit|429/i.test(message)) {
          throw new RunnerRateLimitError("codex", message);
        }
        throw new HarnessError(`codex sdk run failed: ${message}`);
      }
    },
  };
}

async function runThread(
  thread: Thread,
  prompt: string,
  options: {
    runnerName: string;
    timeoutMs?: number;
    heartbeatMs: number;
    stallTimeoutMs: number;
    observability?: TurnObservability;
  },
  logger?: HarnessLogger,
): Promise<ExecutionResult> {
  const controller = new AbortController();
  const timeoutMs = options.timeoutMs;
  const startedAt = Date.now();
  const overallDeadline = timeoutMs ? startedAt + timeoutMs : undefined;
  const timeoutHandle = timeoutMs
    ? setTimeout(() => controller.abort(new Error(`Codex turn timed out after ${timeoutMs}ms.`)), timeoutMs)
    : undefined;
  const input: Input = prompt;
  logger?.log(EVENT.RUNNER_TURN_STARTED, {
    runner: options.runnerName,
    threadId: thread.id,
    timeoutMs: timeoutMs ?? null,
    heartbeatMs: options.heartbeatMs,
    stallTimeoutMs: options.stallTimeoutMs,
    promptChars: prompt.length,
  });

  let streamed: Awaited<ReturnType<Thread["runStreamed"]>>;
  try {
    streamed = await thread.runStreamed(input, { signal: controller.signal });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    logger?.log(EVENT.RUNNER_TRANSPORT_FAILED, {
      runner: options.runnerName,
      threadId: thread.id,
      phase: "runStreamed",
      message,
    });
    if (timeoutHandle) clearTimeout(timeoutHandle);
    throw error;
  }

  let finalText = "";
  let usage: {
    input_tokens: number;
    cached_input_tokens: number;
    output_tokens: number;
    reasoning_output_tokens: number;
  } | null = null;

  const iterator = streamed.events[Symbol.asyncIterator]();
  let nextEvent = iterator.next();
  let firstEventSeen = false;
  let lastEventAt = Date.now();
  let lastHeartbeatAt = Date.now();
  let lastEventType = "none";
  let lastEventSummary = "none";
  const observation = createTurnObservationState();

  try {
    while (true) {
      const winner = await Promise.race([
        nextEvent.then((result) => ({ kind: "event" as const, result })),
        sleep(determineWaitMs(lastEventAt, lastHeartbeatAt, overallDeadline, options.heartbeatMs, options.stallTimeoutMs))
          .then(() => ({ kind: "tick" as const })),
      ]);

      if (winner.kind === "tick") {
        const now = Date.now();
        const idleMs = now - lastEventAt;
        if (overallDeadline && now >= overallDeadline) {
          controller.abort(new Error(`Codex turn timed out after ${timeoutMs}ms.`));
          logger?.log(EVENT.RUNNER_TURN_TIMEOUT, {
            runner: options.runnerName,
            threadId: thread.id,
            elapsedMs: now - startedAt,
            lastEventType,
            lastEventSummary,
          });
          throw new HarnessError(
            `Codex turn timed out after ${timeoutMs}ms (last event: ${lastEventType} / ${lastEventSummary}).`,
          );
        }
        if (idleMs >= options.stallTimeoutMs) {
          controller.abort(new Error(`Codex turn stalled for ${idleMs}ms.`));
          logger?.log(EVENT.RUNNER_TURN_TIMEOUT, {
            runner: options.runnerName,
            threadId: thread.id,
            elapsedMs: now - startedAt,
            idleMs,
            reason: "stall_timeout",
            lastEventType,
            lastEventSummary,
          });
          throw new HarnessError(
            `Codex turn stalled for ${idleMs}ms (last event: ${lastEventType} / ${lastEventSummary}).`,
          );
        }
        if (idleMs >= options.heartbeatMs && now - lastHeartbeatAt >= options.heartbeatMs) {
          lastHeartbeatAt = now;
          logger?.log(EVENT.RUNNER_TURN_STALLED, {
            runner: options.runnerName,
            threadId: thread.id,
            elapsedMs: now - startedAt,
            idleMs,
            lastEventType,
            lastEventSummary,
          });
        }
        continue;
      }

      const { done, value: event } = winner.result;
      if (done) break;

      const now = Date.now();
      lastEventAt = now;
      lastHeartbeatAt = now;
      if (!firstEventSeen) {
        firstEventSeen = true;
        logger?.log(EVENT.RUNNER_TURN_PROGRESS, {
          runner: options.runnerName,
          threadId: thread.id,
          phase: "first_event",
          elapsedMs: now - startedAt,
          eventType: event.type,
        });
      }

      lastEventType = event.type;
      lastEventSummary = summarizeEvent(event);
      captureTurnObservation(observation, event, now - startedAt, options.observability);
      logEventProgress(logger, options.runnerName, thread.id, now - startedAt, event, lastEventSummary);

      if (event.type === "item.completed" && event.item.type === "agent_message") {
        finalText = event.item.text;
      } else if (event.type === "turn.completed") {
        usage = event.usage;
      } else if (event.type === "turn.failed") {
        throw new HarnessError(event.error.message);
      } else if (event.type === "error") {
        throw new HarnessError(event.message);
      }

      nextEvent = iterator.next();
    }
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    emitTurnObservation(logger, options.runnerName, thread.id, options.observability, observation);
    logger?.log(EVENT.RUNNER_TRANSPORT_FAILED, {
      runner: options.runnerName,
      threadId: thread.id,
      elapsedMs: Date.now() - startedAt,
      lastEventType,
      lastEventSummary,
      message,
    });
    throw error;
  } finally {
    if (timeoutHandle) clearTimeout(timeoutHandle);
  }

  if (logger) {
    logger.logCommand("codex-sdk", ["thread.runStreamed"], {
      stdout: finalText,
      stderr: "",
      exitCode: 0,
    });
  }
  emitTurnObservation(logger, options.runnerName, thread.id, options.observability, observation);

  return {
    text: finalText,
    sessionId: thread.id ?? undefined,
    metadata: usage
      ? {
          inputTokens: usage.input_tokens + usage.cached_input_tokens,
          outputTokens: usage.output_tokens,
          cacheReadInputTokens: usage.cached_input_tokens,
        }
      : undefined,
  } satisfies ExecutionResult;
}

function determineWaitMs(
  lastEventAt: number,
  lastHeartbeatAt: number,
  overallDeadline: number | undefined,
  heartbeatMs: number,
  stallTimeoutMs: number,
): number {
  const now = Date.now();
  const waits = [
    heartbeatMs - (now - lastHeartbeatAt),
    stallTimeoutMs - (now - lastEventAt),
  ];
  if (overallDeadline !== undefined) {
    waits.push(overallDeadline - now);
  }
  const positive = waits.filter((value) => Number.isFinite(value) && value > 0);
  return Math.max(250, Math.min(...positive, heartbeatMs));
}

function logEventProgress(
  logger: HarnessLogger | undefined,
  runnerName: string,
  threadId: string | null,
  elapsedMs: number,
  event: ThreadEvent,
  summary: string,
): void {
  if (!logger) return;
  switch (event.type) {
    case "thread.started":
      logger.log(EVENT.RUNNER_TURN_PROGRESS, {
        runner: runnerName,
        threadId: event.thread_id,
        elapsedMs,
        eventType: event.type,
        summary,
      });
      return;
    case "turn.started":
    case "turn.completed":
      logger.log(EVENT.RUNNER_TURN_PROGRESS, {
        runner: runnerName,
        threadId,
        elapsedMs,
        eventType: event.type,
        summary,
      });
      return;
    case "item.started":
    case "item.completed":
      logger.log(EVENT.RUNNER_TURN_PROGRESS, {
        runner: runnerName,
        threadId,
        elapsedMs,
        eventType: event.type,
        itemType: event.item.type,
        summary,
      });
      return;
    default:
      return;
  }
}

function summarizeEvent(event: ThreadEvent): string {
  switch (event.type) {
    case "thread.started":
      return `thread=${event.thread_id}`;
    case "turn.started":
      return "turn started";
    case "turn.completed":
      return `usage in=${event.usage.input_tokens + event.usage.cached_input_tokens} out=${event.usage.output_tokens}`;
    case "turn.failed":
      return event.error.message;
    case "error":
      return event.message;
    case "item.started":
    case "item.updated":
    case "item.completed":
      return summarizeItem(event.item);
  }
}

function summarizeItem(item: ThreadItem): string {
  switch (item.type) {
    case "command_execution":
      return `command status=${item.status} cmd=${item.command}`;
    case "file_change":
      return `file_change status=${item.status} count=${item.changes.length}`;
    case "mcp_tool_call":
      return `mcp ${item.server}/${item.tool} status=${item.status}`;
    case "agent_message":
      return `agent_message chars=${item.text.length}`;
    case "reasoning":
      return `reasoning chars=${item.text.length}`;
    case "todo_list":
      return `todo_list items=${item.items.length}`;
    case "web_search":
      return `web_search query=${item.query}`;
    case "error":
      return `error ${item.message}`;
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function createTurnObservationState(): TurnObservationState {
  return {
    firstCommand: null,
    firstCommandElapsedMs: null,
    firstFileChangeElapsedMs: null,
    firstFileChangePaths: [],
    primaryTargetFileTouched: false,
    primaryTargetFileTouchedElapsedMs: null,
    nonTargetFileChangeObserved: false,
    preTargetExplorationObserved: false,
    preTargetCommandSummaries: [],
  };
}

function captureTurnObservation(
  state: TurnObservationState,
  event: ThreadEvent,
  elapsedMs: number,
  observability?: TurnObservability,
): void {
  if (event.type !== "item.started" && event.type !== "item.completed") return;

  if (event.item.type === "command_execution") {
    if (event.type !== "item.started") return;
    if (state.firstCommand === null) {
      state.firstCommand = event.item.command;
      state.firstCommandElapsedMs = elapsedMs;
    }
    if (!state.primaryTargetFileTouched && shouldFlagPreTargetExploration(event.item.command, observability)) {
      state.preTargetExplorationObserved = true;
      if (state.preTargetCommandSummaries.length < 5) {
        state.preTargetCommandSummaries.push(event.item.command);
      }
    }
    return;
  }

  if (event.item.type !== "file_change" || event.item.status !== "completed") return;

  const changedPaths = extractChangedPaths(event.item);
  if (state.firstFileChangeElapsedMs === null) {
    state.firstFileChangeElapsedMs = elapsedMs;
    state.firstFileChangePaths = changedPaths;
  }
  const primaryTargetFile = normalizeRepoPath(observability?.primaryTargetFile);
  const touchedPrimaryTarget = primaryTargetFile !== null
    && changedPaths.some((path) => pathMatchesPrimaryTarget(path, primaryTargetFile));
  if (touchedPrimaryTarget && !state.primaryTargetFileTouched) {
    state.primaryTargetFileTouched = true;
    state.primaryTargetFileTouchedElapsedMs = elapsedMs;
  }
  if (changedPaths.some((path) => !pathMatchesPrimaryTarget(path, primaryTargetFile))) {
    state.nonTargetFileChangeObserved = true;
  }
}

function emitTurnObservation(
  logger: HarnessLogger | undefined,
  runnerName: string,
  threadId: string | null,
  observability: TurnObservability | undefined,
  state: TurnObservationState,
): void {
  if (!logger || !observability?.step) return;
  logger.log(EVENT.RUNNER_TURN_OBSERVATION, {
    runner: runnerName,
    threadId,
    step: observability.step,
    benchmarkMode: observability.benchmarkMode ?? null,
    primaryTargetFile: observability.primaryTargetFile ?? null,
    firstCommand: state.firstCommand,
    firstCommandElapsedMs: state.firstCommandElapsedMs,
    firstFileChangeElapsedMs: state.firstFileChangeElapsedMs,
    firstFileChangePaths: state.firstFileChangePaths,
    primaryTargetFileTouched: state.primaryTargetFileTouched,
    primaryTargetFileTouchedElapsedMs: state.primaryTargetFileTouchedElapsedMs,
    nonTargetFileChangeObserved: state.nonTargetFileChangeObserved,
    preTargetExplorationObserved: state.preTargetExplorationObserved,
    preTargetCommandSummaries: state.preTargetCommandSummaries,
  });
}

function shouldFlagPreTargetExploration(
  command: string,
  observability?: TurnObservability,
): boolean {
  const relevantFiles = [
    observability?.primaryTargetFile,
    ...(observability?.relatedFiles ?? []),
  ]
    .map((value) => normalizeRepoPath(value))
    .filter((value): value is string => value !== null);
  if (relevantFiles.some((file) => command.includes(file))) {
    return false;
  }
  return /\b(pwd|ls|find|rg|grep|git)\b/.test(command)
    || command.includes("../")
    || command.includes("pyproject.toml")
    || command.includes("package.json");
}

function extractChangedPaths(item: Extract<ThreadItem, { type: "file_change" }>): string[] {
  return item.changes
    .map((change) => {
      const candidate = change as Record<string, unknown>;
      const path = candidate.path ?? candidate.file_path ?? candidate.target_path;
      return typeof path === "string" ? path : null;
    })
    .filter((value): value is string => value !== null);
}

function normalizeRepoPath(value: string | undefined): string | null {
  if (!value) return null;
  return value.replace(/\\/g, "/").replace(/^\.?\//, "");
}

function pathMatchesPrimaryTarget(path: string, primaryTargetFile: string | null): boolean {
  if (!primaryTargetFile) return false;
  const normalizedPath = normalizeRepoPath(path);
  if (!normalizedPath) return false;
  return normalizedPath === primaryTargetFile || normalizedPath.endsWith(`/${primaryTargetFile}`);
}
