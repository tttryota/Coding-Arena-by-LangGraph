import { STEP_ORDER } from "../types.ts";
import type { CompletedStep } from "../types.ts";

export function shouldSkipStep(
  completedStep: CompletedStep | null,
  target: CompletedStep,
): boolean {
  if (!completedStep) return false;
  return STEP_ORDER.indexOf(completedStep) >= STEP_ORDER.indexOf(target);
}
