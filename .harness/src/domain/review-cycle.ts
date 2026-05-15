import {
  hasParseFailure,
  isMinorOnly,
  shouldEscalateReview,
  shouldJudgeMinorAcceptance,
} from "./review-acceptance-policy.ts";
import type { ReviewIssue, ReviewResult } from "../types.ts";

type ReviewCycleDecision = {
  cycle: number;
  issueCount: number;
  isLgtm: boolean;
  minorOnlyCycles: number;
};

export class ReviewCycle {
  private cycle: number;
  private minorOnlyCycles: number;
  private lastIssues: ReviewIssue[];
  private lastLgtm: boolean;
  private decisionLog: ReviewCycleDecision[];

  constructor() {
    this.cycle = 0;
    this.minorOnlyCycles = 0;
    this.lastIssues = [];
    this.lastLgtm = false;
    this.decisionLog = [];
  }

  record(result: Pick<ReviewResult, "issues" | "isLgtm">): void {
    this.cycle += 1;
    this.lastIssues = [...result.issues];
    this.lastLgtm = result.isLgtm;

    if (result.isLgtm) {
      this.minorOnlyCycles = 0;
    } else if (isMinorOnly(result.issues)) {
      this.minorOnlyCycles += 1;
    } else {
      this.minorOnlyCycles = 0;
    }

    this.decisionLog.push({
      cycle: this.cycle,
      issueCount: result.issues.length,
      isLgtm: result.isLgtm,
      minorOnlyCycles: this.minorOnlyCycles,
    });
  }

  getCycle(): number {
    return this.cycle;
  }

  getMinorOnlyCycles(): number {
    return this.minorOnlyCycles;
  }

  getLastIssues(): ReviewIssue[] {
    return [...this.lastIssues];
  }

  getDecisionLog(): ReviewCycleDecision[] {
    return [...this.decisionLog];
  }

  isLgtm(): boolean {
    return this.lastLgtm;
  }

  hasParseFailure(): boolean {
    return hasParseFailure(this.lastIssues);
  }

  shouldJudgeMinorAcceptance(): boolean {
    return shouldJudgeMinorAcceptance(this.minorOnlyCycles);
  }

  shouldEscalate(maxCycles: number): boolean {
    return shouldEscalateReview(this.cycle, maxCycles);
  }
}
