import { mkdirSync, appendFileSync, writeFileSync, readFileSync, existsSync, unlinkSync } from "node:fs";
import { join } from "node:path";
import type { CommandResult, CheckpointData } from "./types.ts";

type LoggerOptions = {
  baseDir?: string;
  redactOutput?: boolean;
};

const REDACT_PATTERNS = [
  // Anthropic
  /sk-ant-[a-zA-Z0-9_-]{20,}/g,
  /sk-[a-zA-Z0-9_-]{20,}/g,
  /ANTHROPIC_API_KEY\s*=\s*\S+/g,
  // OpenAI
  /sk-proj-[a-zA-Z0-9_-]{20,}/g,
  /sess-[a-zA-Z0-9_-]{20,}/g,
  // GitHub PAT
  /ghp_[a-zA-Z0-9]{36,}/g,
  /github_pat_[a-zA-Z0-9_]{20,}/g,
  /gho_[a-zA-Z0-9]{36,}/g,
  // AWS
  /AKIA[A-Z0-9]{16}/g,
  /aws_secret_access_key\s*=\s*\S+/gi,
  // Generic
  /Bearer\s+[a-zA-Z0-9._-]+/g,
  /xoxb-[a-zA-Z0-9-]+/g,
  /xoxp-[a-zA-Z0-9-]+/g,
];

export function redact(text: string): string {
  let result = text;
  for (const pattern of REDACT_PATTERNS) {
    result = result.replace(pattern, "[REDACTED]");
  }
  return result;
}

export class HarnessLogger {
  private logDir: string;
  private harnessLogPath: string;
  private redactOutput: boolean;

  constructor(taskName: string, options?: LoggerOptions) {
    const baseDir = options?.baseDir ?? "logs";
    this.redactOutput = options?.redactOutput ?? true;

    // パストラバーサル防止: taskName から危険な文字を除去
    const sanitized = taskName.replace(/[./\\]/g, "_");
    const timestamp = new Date()
      .toISOString()
      .replace(/[:.]/g, "-")
      .slice(0, 19);
    this.logDir = join(baseDir, `${timestamp}_${sanitized}`);
    mkdirSync(this.logDir, { recursive: true });
    this.harnessLogPath = join(this.logDir, "harness.jsonl");
  }

  log(event: string, data?: Record<string, unknown>): void {
    const entry = {
      ts: new Date().toISOString(),
      event,
      ...data,
    };
    const line = this.redactOutput
      ? redact(JSON.stringify(entry))
      : JSON.stringify(entry);
    appendFileSync(this.harnessLogPath, line + "\n", "utf-8");
  }

  logCommand(
    tool: string,
    args: string[],
    result: CommandResult,
  ): void {
    const logFileName =
      tool === "codex" ? "codex-review.log" : "claude-code.log";
    const logPath = join(this.logDir, logFileName);
    const rawEntry = [
      `=== ${new Date().toISOString()} ===`,
      `Command: ${tool} ${args.join(" ")}`,
      `Exit code: ${result.exitCode}`,
      `--- stdout ---`,
      result.stdout,
      `--- stderr ---`,
      result.stderr,
      "",
    ].join("\n");
    const entry = this.redactOutput ? redact(rawEntry) : rawEntry;
    appendFileSync(logPath, entry, "utf-8");
  }

  saveReviewData(data: unknown): void {
    const dataPath = join(this.logDir, "review-data.json");
    const content = JSON.stringify(data, null, 2);
    writeFileSync(dataPath, this.redactOutput ? redact(content) : content, "utf-8");
  }

  saveCheckpoint(data: CheckpointData): void {
    const checkpointPath = join(this.logDir, "checkpoint.json");
    writeFileSync(checkpointPath, JSON.stringify(data, null, 2), "utf-8");
  }

  loadCheckpoint(): CheckpointData | null {
    const checkpointPath = join(this.logDir, "checkpoint.json");
    if (!existsSync(checkpointPath)) return null;
    try {
      return JSON.parse(readFileSync(checkpointPath, "utf-8")) as CheckpointData;
    } catch {
      return null;
    }
  }

  clearCheckpoint(): void {
    const checkpointPath = join(this.logDir, "checkpoint.json");
    if (existsSync(checkpointPath)) {
      unlinkSync(checkpointPath);
    }
  }

  getLogDir(): string {
    return this.logDir;
  }
}
