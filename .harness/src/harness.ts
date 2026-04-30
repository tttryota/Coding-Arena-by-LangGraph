import { resolve, join } from "node:path";
import { HarnessLogger } from "./logger.ts";
import { Boundary } from "./boundary.ts";
import { DesignFlow } from "./design-flow.ts";
import { ImplFlow } from "./impl-flow.ts";

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const command = args[0];

  if (!command) {
    console.log("Usage:");
    console.log("  ./harness impl <plan-file>");
    console.log('  ./harness design <feature-name> "<requirements>"');
    process.exit(1);
  }

  // import.meta.dirname = .harness/src → "../.." でリポジトリルートへ
  const projectRoot = resolve(
    import.meta.dirname ?? process.cwd(),
    "..",
    "..",
  );
  const boundary = new Boundary(projectRoot);

  switch (command) {
    case "impl": {
      const planPath = args[1];
      if (!planPath) {
        console.error("Error: plan file path required");
        process.exit(1);
      }
      const implFlow = new ImplFlow(boundary);
      await implFlow.run(planPath);
      break;
    }
    case "design": {
      const featureName = args[1];
      const requirements = args[2];
      if (!featureName || !requirements) {
        console.error('Error: feature name and requirements required');
        process.exit(1);
      }
      const logger = new HarnessLogger(`design_${featureName}`, { baseDir: join(projectRoot, "logs") });
      const designFlow = new DesignFlow(boundary);
      await designFlow.run(featureName, requirements, logger);
      break;
    }
    default:
      console.error(`Unknown command: ${command}`);
      process.exit(1);
  }
}

main().catch((error: unknown) => {
  console.error("Harness error:", error);
  process.exit(1);
});
