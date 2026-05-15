import type { ReviewIssue } from "../types.ts";

export const MINOR_ACCEPTANCE_CYCLE_THRESHOLD = 2;

export function hasParseFailure(issues: ReviewIssue[]): boolean {
  return issues.some((issue) => issue.file === "" && issue.severity === "critical");
}

export function hasCriticalOrMajor(issues: ReviewIssue[]): boolean {
  return issues.some((issue) => issue.severity === "critical" || issue.severity === "major");
}

export function isMinorOnly(issues: ReviewIssue[]): boolean {
  return issues.length > 0 && !hasCriticalOrMajor(issues);
}

export function shouldJudgeMinorAcceptance(minorOnlyCycles: number): boolean {
  return minorOnlyCycles >= MINOR_ACCEPTANCE_CYCLE_THRESHOLD;
}

export function shouldEscalateReview(cycle: number, maxCycles: number): boolean {
  return cycle >= maxCycles;
}
