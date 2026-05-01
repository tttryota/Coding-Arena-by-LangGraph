// === claude -p の JSON 出力 ===

export type ClaudeResult = {
  result: string;
  session_id: string;
  is_error: boolean;
  total_cost_usd: number | null;
  usage: { input_tokens: number; output_tokens: number };
};

// === エスカレーション ===

export const ESCALATION_LEVEL = {
  LEVEL_1: 1,
  LEVEL_2: 2,
  LEVEL_3: 3,
} as const;

export type EscalationLevel =
  (typeof ESCALATION_LEVEL)[keyof typeof ESCALATION_LEVEL];

// === 例外 ===

export class HarnessError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "HarnessError";
  }
}

export class DriftError extends HarnessError {
  level: EscalationLevel;
  metric: string;

  constructor(level: EscalationLevel, metric: string, message: string) {
    super(message);
    this.name = "DriftError";
    this.level = level;
    this.metric = metric;
  }
}

export class GuardError extends HarnessError {
  constructor(message: string) {
    super(message);
    this.name = "GuardError";
  }
}

// === リント ===

export type LintViolation = {
  tool: string;
  file: string;
  line: number;
  message: string;
};

// === レビュー ===

export type ReviewIssue = {
  description: string;
  severity: "critical" | "major" | "minor";
  file: string;
  line?: number;
};

export type ReviewResult = {
  reviewer: string;
  issues: ReviewIssue[];
  isLgtm: boolean;
};

// === 計画ファイル ===

export type TaskPlan = {
  scope: string;
  specPath: string;
  testCasesPath: string;
  description: string;
  targetTestCases: string[];
  exclusions: string[];
  completionCriteria: string[];
  designDecisions: string[];
};

// === レビューレポート ===

export type ReviewRecord = {
  step: string;
  cycle: number;
  reviewer: string;
  findings: ReviewIssue[];
  decision: "fixed" | "accepted" | "escalated" | "lgtm";
  diffBefore: string;
  diffAfter: string;
  judgmentSummary: string;
};

// === コマンド実行結果 ===

export type CommandResult = {
  stdout: string;
  stderr: string;
  exitCode: number;
};

// === チェックポイント ===

export const STEP_ORDER = [
  "test_generated",
  "test_reviewed",
  "red_confirmed",
  "green_confirmed",
  "impl_reviewed",
] as const;

export type CompletedStep = (typeof STEP_ORDER)[number];

export type CheckpointData = {
  planPath: string;
  completedStep: CompletedStep;
  sessionId: string;
  records: ReviewRecord[];
  greenAttempt: number;
  timestamp: string;
};

// === ログイベント定数 ===

export const EVENT = {
  GUARD_CHECK: "guard_check",
  TDD_START: "tdd_start",
  CLAUDE_P_CALL: "claude_p_call",
  TEST_RUN: "test_run",
  LINT_VIOLATIONS: "lint_violations",
  LINT_PASSED: "lint_passed",
  SELF_REVIEW: "self_review",
  REVIEW_START: "review_start",
  CODEX_RATE_LIMITED: "codex_rate_limited",
  CLAUDE_REVIEW: "claude_review",
  REVIEW_RECONCILED: "review_reconciled",
  DRIFT_DETECTED: "drift_detected",
  ESCALATION_TO_HUMAN: "escalation_to_human",
} as const;
