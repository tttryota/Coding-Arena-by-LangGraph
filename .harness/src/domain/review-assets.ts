import { existsSync, readFileSync } from "node:fs";
import { join, resolve } from "node:path";
import type { ResolvedProfileConfig } from "../config.ts";
import { GuardError } from "../types.ts";

type ReviewCriteriaFallback = "backend" | "frontend";

export function resolveReviewCriteriaPaths(
  projectRoot: string,
  profile: Pick<ResolvedProfileConfig, "reviewCriteria" | "criteriaPreset">,
  fallbackPreset: ReviewCriteriaFallback,
): string[] {
  const paths: string[] = [];

  for (const criteriaPath of profile.reviewCriteria) {
    const fullPath = resolve(projectRoot, criteriaPath);
    if (!existsSync(fullPath)) {
      throw new GuardError(`Review criteria not found: ${criteriaPath}`);
    }
    paths.push(fullPath);
  }

  if (profile.criteriaPreset) {
    for (const name of ["review-criteria-common", `review-criteria-${profile.criteriaPreset}`]) {
      paths.push(resolveRequiredHarnessAssetPath(projectRoot, name));
    }
  }

  if (paths.length === 0) {
    for (const name of ["review-criteria-common", `review-criteria-${fallbackPreset}`]) {
      const resolved = resolveOptionalHarnessAssetPath(projectRoot, name);
      if (resolved) paths.push(resolved);
    }
  }

  return paths;
}

export function readOptionalRulesContent(projectRoot: string, ruleName: string | undefined): string {
  if (!ruleName) return "";
  const resolved = resolveOptionalHarnessAssetPath(projectRoot, `rules/${ruleName}.md`, {
    projectInHarnessDir: true,
  });
  return resolved ? readFileSync(resolved, "utf-8") : "";
}

export function resolveRequiredHarnessAssetPath(
  projectRoot: string,
  packageRelativePath: string,
  options?: { projectInHarnessDir?: boolean },
): string {
  const resolved = resolveOptionalHarnessAssetPath(projectRoot, packageRelativePath, options);
  if (resolved) return resolved;
  throw new GuardError(`Harness asset not found: ${packageRelativePath}`);
}

export function resolveOptionalHarnessAssetPath(
  projectRoot: string,
  packageRelativePath: string,
  options?: { projectInHarnessDir?: boolean },
): string | null {
  const projectPath = options?.projectInHarnessDir === false
    ? join(projectRoot, packageRelativePath)
    : join(projectRoot, ".harness", packageRelativePath);
  if (existsSync(projectPath)) return projectPath;

  const packagePath = join(import.meta.dirname ?? "", "..", "..", packageRelativePath);
  if (existsSync(packagePath)) return packagePath;

  return null;
}
