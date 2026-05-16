#!/usr/bin/env node
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { HarnessLogger, DEFAULT_LOG_BASE_DIR } from "../infrastructure/logging/logger.ts";
import { HarnessError } from "../domain/model/types.ts";
import { Boundary } from "../domain/services/boundary.ts";
import { DesignFlow } from "../application/flows/design-flow.ts";
import { ComponentFlow } from "../application/flows/component-flow.ts";
import { ImplFlow } from "../application/flows/impl-flow.ts";
import { PageFlow } from "../application/flows/page-flow.ts";
import { loadConfig, inferProfile, resolveProfile } from "../infrastructure/config/config.ts";
import { createRunnerRegistry } from "../infrastructure/runners/runner-registry.ts";
import { interactiveRunnerAssignment } from "./interactive.ts";
import { parsePlan } from "../domain/services/plan-parser.ts";
import { resolveLintAdapter, resolveTestAdapter } from "../infrastructure/tooling/tool-adapter.ts";
import type { BaseAdapter } from "../infrastructure/tooling/tool-adapter.ts";
import type { FlowMode, FlowStep } from "../domain/model/steps.ts";
import { renderBenchmarkSummary } from "../application/diagnostics/benchmark-summary.ts";
import { renderBenchmarkDiagnose } from "../application/diagnostics/benchmark-diagnose.ts";

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const command = args[0];

  if (!command) {
    console.log("Usage:");
    console.log("  tdd-harness impl <plan-file> [--resume] [--flow full|light] [--no-interactive]");
    console.log("  tdd-harness component <plan-file> [--flow full|light] [--no-interactive]");
    console.log("  tdd-harness page <plan-file> [--flow full|light] [--no-interactive]");
    console.log('  tdd-harness design <feature-name> "<requirements>" [--profile <name>]');
    console.log("  tdd-harness benchmark-summary <log-dir> [<log-dir>]");
    console.log("  tdd-harness benchmark-diagnose <log-dir> [<log-dir>]");
    console.log("  tdd-harness init");
    process.exit(1);
  }

  const projectRoot = process.cwd();
  const config = loadConfig(projectRoot);

  switch (command) {
    case "impl": {
      const planPath = args[1];
      if (!planPath) {
        console.error("Error: plan file path required");
        process.exit(1);
      }
      const resume = args.includes("--resume");
      const noInteractive = args.includes("--no-interactive");
      const flowFlagIndex = args.indexOf("--flow");
      const flowFlag = flowFlagIndex !== -1 ? args[flowFlagIndex + 1] as FlowMode | undefined : undefined;

      // 1. plan を先に読む（Boundary 不要）
      const plan = parsePlan(projectRoot, planPath);

      // 2. profile 解決
      const profileName = plan.profile ?? inferProfile(config);
      const profile = resolveProfile(config, profileName);
      const effectiveFlow = flowFlag ?? profile.flow;

      // 3. adapter 解決
      const lintAdapters = profile.lint.map(resolveLintAdapter);
      const testAdapter = resolveTestAdapter(profile.test);
      const allAdapters: BaseAdapter[] = [...lintAdapters, testAdapter];
      const extensions = [...new Set(allAdapters.flatMap((a) => [...a.fileExtensions]))];
      const excludeDirs = [...new Set(allAdapters.flatMap((a) => [...a.excludeDirs]))];

      // 4. profile-aware な Boundary を組み立て
      const boundary = new Boundary(projectRoot, profile.sourceLayout, extensions, excludeDirs);

      let overrides: Partial<Record<FlowStep, string>> | null = null;
      if (!noInteractive && !resume && process.stdin.isTTY) {
        overrides = await interactiveRunnerAssignment(Object.keys(config.runners), profile.steps, effectiveFlow);
      }

      const registry = createRunnerRegistry(config, projectRoot, profile, overrides ?? undefined, effectiveFlow);

      // 5. ImplFlow 実行
      const implFlow = new ImplFlow(boundary, registry, profile, testAdapter, lintAdapters);
      await implFlow.run(planPath, { resume, plan });
      break;
    }
    case "page": {
      const planPath = args[1];
      if (!planPath) {
        console.error("Error: plan file path required");
        process.exit(1);
      }
      const noInteractive = args.includes("--no-interactive");
      const flowFlagIndex = args.indexOf("--flow");
      const flowFlag = flowFlagIndex !== -1 ? args[flowFlagIndex + 1] as FlowMode | undefined : undefined;

      const plan = parsePlan(projectRoot, planPath);
      const profileName = plan.profile ?? inferProfile(config);
      const profile = resolveProfile(config, profileName);
      const effectiveFlow = flowFlag ?? profile.flow;
      const lintAdapters = profile.lint.map(resolveLintAdapter);
      const testAdapter = resolveTestAdapter(profile.test);
      const allAdapters: BaseAdapter[] = [...lintAdapters, testAdapter];
      const extensions = [...new Set(allAdapters.flatMap((a) => [...a.fileExtensions]))];
      const excludeDirs = [...new Set(allAdapters.flatMap((a) => [...a.excludeDirs]))];
      const boundary = new Boundary(projectRoot, profile.sourceLayout, extensions, excludeDirs);

      let overrides: Partial<Record<FlowStep, string>> | null = null;
      if (!noInteractive && process.stdin.isTTY) {
        overrides = await interactiveRunnerAssignment(Object.keys(config.runners), profile.steps, effectiveFlow);
      }

      const registry = createRunnerRegistry(config, projectRoot, profile, overrides ?? undefined, effectiveFlow);
      const pageFlow = new PageFlow(boundary, registry, profile, testAdapter, lintAdapters);
      await pageFlow.run(planPath, { plan });
      break;
    }
    case "component": {
      const planPath = args[1];
      if (!planPath) {
        console.error("Error: plan file path required");
        process.exit(1);
      }
      const noInteractive = args.includes("--no-interactive");
      const flowFlagIndex = args.indexOf("--flow");
      const flowFlag = flowFlagIndex !== -1 ? args[flowFlagIndex + 1] as FlowMode | undefined : undefined;

      const plan = parsePlan(projectRoot, planPath);
      const profileName = plan.profile ?? inferProfile(config);
      const profile = resolveProfile(config, profileName);
      const effectiveFlow = flowFlag ?? profile.flow;
      const lintAdapters = profile.lint.map(resolveLintAdapter);
      const testAdapter = resolveTestAdapter(profile.test);
      const allAdapters: BaseAdapter[] = [...lintAdapters, testAdapter];
      const extensions = [...new Set(allAdapters.flatMap((a) => [...a.fileExtensions]))];
      const excludeDirs = [...new Set(allAdapters.flatMap((a) => [...a.excludeDirs]))];
      const boundary = new Boundary(projectRoot, profile.sourceLayout, extensions, excludeDirs);

      let overrides: Partial<Record<FlowStep, string>> | null = null;
      if (!noInteractive && process.stdin.isTTY) {
        overrides = await interactiveRunnerAssignment(Object.keys(config.runners), profile.steps, effectiveFlow);
      }

      const registry = createRunnerRegistry(config, projectRoot, profile, overrides ?? undefined, effectiveFlow);
      const componentFlow = new ComponentFlow(boundary, registry, profile, testAdapter, lintAdapters);
      await componentFlow.run(planPath, { plan });
      break;
    }
    case "design": {
      const featureName = args[1];
      const requirements = args[2];
      if (!featureName || !requirements) {
        console.error('Error: feature name and requirements required');
        process.exit(1);
      }
      const profileFlagIndex = args.indexOf("--profile");
      const profileName = profileFlagIndex !== -1 ? args[profileFlagIndex + 1] : undefined;
      const boundary = new Boundary(projectRoot);
      const logger = new HarnessLogger(`design_${featureName}`, { baseDir: join(projectRoot, DEFAULT_LOG_BASE_DIR) });
      const profile = resolveProfile(
        config,
        profileName ?? inferProfile(config),
      );
      const registry = createRunnerRegistry(config, projectRoot, profile);
      const designFlow = new DesignFlow(boundary, registry, profile);
      await designFlow.run(featureName, requirements, logger);
      break;
    }
    case "benchmark-summary": {
      const logDirs = args.slice(1);
      if (logDirs.length === 0 || logDirs.length > 2) {
        console.error("Error: benchmark-summary requires one or two log directories");
        process.exit(1);
      }
      console.log(renderBenchmarkSummary(logDirs));
      break;
    }
    case "benchmark-diagnose": {
      const logDirs = args.slice(1);
      if (logDirs.length === 0 || logDirs.length > 2) {
        console.error("Error: benchmark-diagnose requires one or two log directories");
        process.exit(1);
      }
      console.log(renderBenchmarkDiagnose(logDirs, projectRoot));
      break;
    }
    case "init": {
      const guidePath = join(import.meta.dirname ?? "", "..", "..", "setup-guide.md");
      try {
        console.log(readFileSync(guidePath, "utf-8"));
      } catch {
        console.error("setup-guide.md が見つかりません。パッケージが正しくインストールされていることを確認してください。");
        process.exit(1);
      }
      break;
    }
    default:
      console.error(`Unknown command: ${command}`);
      process.exit(1);
  }
}

main().catch((error: unknown) => {
  if (error instanceof HarnessError) {
    console.error(`[${error.name}] ${error.message}`);
  } else {
    console.error("Unexpected error:", error);
  }
  process.exit(1);
});
