#!/usr/bin/env node
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { HarnessError } from "../shared/types.ts";
import type { FlowMode, FlowStep } from "../shared/steps.ts";
import {
  runBenchmarkSummaryCommand,
  runComponentCommand,
  runDesignCommand,
  runImplCommand,
  runPageCommand,
} from "../application/commands/harness-commands.ts";

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const command = args[0];

  if (!command) {
    console.log("Usage:");
    console.log("  tdd-harness impl <plan-file> [--profile <name>] [--resume] [--flow full|light] [--no-interactive]");
    console.log("  tdd-harness component <plan-file> [--profile <name>] [--flow full|light] [--no-interactive]");
    console.log("  tdd-harness page <plan-file> [--profile <name>] [--flow full|light] [--no-interactive]");
    console.log('  tdd-harness design <feature-name> "<requirements>" [--profile <name>]');
    console.log("  tdd-harness benchmark-summary <log-dir> [<log-dir>]");
    console.log("  tdd-harness init");
    process.exit(1);
  }

  const projectRoot = process.cwd();

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
      const profileFlagIndex = args.indexOf("--profile");
      const profileOverride = profileFlagIndex !== -1 ? args[profileFlagIndex + 1] : undefined;

      await runImplCommand({
        projectRoot,
        planPath,
        flow: flowFlag,
        profileOverride,
        noInteractive,
        resume,
      });
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
      const profileFlagIndex = args.indexOf("--profile");
      const profileOverride = profileFlagIndex !== -1 ? args[profileFlagIndex + 1] : undefined;

      await runPageCommand({
        projectRoot,
        planPath,
        flow: flowFlag,
        profileOverride,
        noInteractive,
      });
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
      const profileFlagIndex = args.indexOf("--profile");
      const profileOverride = profileFlagIndex !== -1 ? args[profileFlagIndex + 1] : undefined;

      await runComponentCommand({
        projectRoot,
        planPath,
        flow: flowFlag,
        profileOverride,
        noInteractive,
      });
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
      await runDesignCommand({
        projectRoot,
        featureName,
        requirements,
        profileName,
      });
      break;
    }
    case "benchmark-summary": {
      const logDirs = args.slice(1);
      if (logDirs.length === 0 || logDirs.length > 2) {
        console.error("Error: benchmark-summary requires one or two log directories");
        process.exit(1);
      }
      console.log(runBenchmarkSummaryCommand(logDirs));
      break;
    }
    case "init": {
      const guidePath = join(import.meta.dirname ?? "", "..", "setup-guide.md");
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
