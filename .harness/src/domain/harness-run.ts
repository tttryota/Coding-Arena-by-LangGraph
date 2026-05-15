import type { CheckpointData, CompletedStep, ReviewRecord } from "../types.ts";

type HarnessRunParams = {
  planPath: string;
  scope: string;
  completedStep?: CompletedStep | null;
  sessionId?: string;
  greenAttempt?: number;
  reviewRecords?: ReviewRecord[];
  alreadyGreen?: boolean;
};

export class HarnessRun {
  private planPath: string;
  private scope: string;
  private completedStep: CompletedStep | null;
  private sessionId: string;
  private greenAttempt: number;
  private reviewRecords: ReviewRecord[];
  private alreadyGreen: boolean;

  constructor(params: HarnessRunParams) {
    this.planPath = params.planPath;
    this.scope = params.scope;
    this.completedStep = params.completedStep ?? null;
    this.sessionId = params.sessionId ?? "";
    this.greenAttempt = params.greenAttempt ?? 0;
    this.reviewRecords = [...(params.reviewRecords ?? [])];
    this.alreadyGreen = params.alreadyGreen ?? false;
  }

  static restore(
    planPath: string,
    scope: string,
    checkpoint: CheckpointData | null,
  ): HarnessRun {
    if (!checkpoint) {
      return new HarnessRun({ planPath, scope });
    }
    return new HarnessRun({
      planPath,
      scope,
      completedStep: checkpoint.completedStep,
      sessionId: checkpoint.sessionId,
      greenAttempt: checkpoint.greenAttempt,
      reviewRecords: checkpoint.records,
    });
  }

  getPlanPath(): string {
    return this.planPath;
  }

  getScope(): string {
    return this.scope;
  }

  getCompletedStep(): CompletedStep | null {
    return this.completedStep;
  }

  getSessionId(): string {
    return this.sessionId;
  }

  getGreenAttempt(): number {
    return this.greenAttempt;
  }

  getReviewRecords(): ReviewRecord[] {
    return [...this.reviewRecords];
  }

  isAlreadyGreen(): boolean {
    return this.alreadyGreen;
  }

  setSessionId(sessionId: string): void {
    this.sessionId = sessionId;
  }

  advanceTo(step: CompletedStep): void {
    this.completedStep = step;
  }

  markAlreadyGreen(): void {
    this.alreadyGreen = true;
  }

  markGreen(attempt: number): void {
    this.greenAttempt = attempt;
    this.alreadyGreen = false;
    this.advanceTo("green_confirmed");
  }

  replaceReviewRecords(records: ReviewRecord[]): void {
    this.reviewRecords = [...records];
  }

  toCheckpointPayload(timestamp: string): CheckpointData {
    if (!this.completedStep) {
      throw new Error("completedStep が未設定のため checkpoint を作成できません。");
    }
    return {
      planPath: this.planPath,
      completedStep: this.completedStep,
      sessionId: this.sessionId,
      records: [...this.reviewRecords],
      greenAttempt: this.greenAttempt,
      timestamp,
    };
  }
}
