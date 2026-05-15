import { STEP_ORDER } from "../../shared/types.ts";
import type { CompletedStep } from "../../shared/types.ts";

export function shouldSkipStep(
  completedStep: CompletedStep | null,
  target: CompletedStep,
): boolean {
  if (!completedStep) return false;
  return STEP_ORDER.indexOf(completedStep) >= STEP_ORDER.indexOf(target);
}
