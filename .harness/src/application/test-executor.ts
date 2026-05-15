import { resolve } from "node:path";
import { runTool } from "../launcher.ts";
import type { LauncherOptions } from "../launcher.ts";
import { GuardError } from "../types.ts";
import type { TestAdapter } from "../tool-adapter.ts";

export type TestRunResult = {
  passed: boolean;
  output: string;
};

type TestExecutorOptions = {
  projectRoot: string;
  toolRoot: string;
  execOverride: string[];
  collectionErrorMessage?: string;
  noTestsMessage?: string;
  genericFailureMessage?: string;
};

export class TestExecutor {
  private adapter: TestAdapter;
  private options: TestExecutorOptions;

  constructor(adapter: TestAdapter, options: TestExecutorOptions) {
    this.adapter = adapter;
    this.options = options;
  }

  async run(
    testPath: string,
    options?: {
      allowCollectionError?: boolean;
      collectionErrorMessage?: string;
      noTestsMessage?: string;
      genericFailureMessage?: string;
    },
  ): Promise<TestRunResult> {
    const absTestPath = resolve(this.options.projectRoot, testPath);
    const args = this.adapter.buildArgs(absTestPath);
    const launcherOptions: LauncherOptions = {
      toolRoot: this.options.toolRoot,
      execOverride: this.options.execOverride,
    };
    const result = await runTool(this.adapter.name, args, launcherOptions);
    const testResult = this.adapter.parseResult(
      result.stdout,
      result.stderr,
      result.exitCode,
    );

    switch (testResult.kind) {
      case "passed":
        return { passed: true, output: testResult.output };
      case "failed":
        return { passed: false, output: testResult.output };
      case "collection-error":
        if (options?.allowCollectionError) {
          return { passed: false, output: testResult.output };
        }
        throw new GuardError(
          withOutput(
            options?.collectionErrorMessage
              ?? this.options.collectionErrorMessage
              ?? `${this.adapter.frameworkName} がコレクションエラーで終了しました。環境を確認してください。`,
            testResult.output,
          ),
        );
      case "no-tests":
        throw new GuardError(
          withOutput(
            options?.noTestsMessage
              ?? this.options.noTestsMessage
              ?? `${this.adapter.frameworkName} がテスト未検出で終了しました。テストパスを確認してください。`,
            testResult.output,
          ),
        );
      case "internal-error":
      case "interrupted":
        throw new GuardError(
          withOutput(
            options?.genericFailureMessage
              ?? this.options.genericFailureMessage
              ?? `${this.adapter.frameworkName} が内部エラーで終了しました (exit ${testResult.exitCode})。`,
            testResult.output,
          ),
        );
    }
  }
}

function withOutput(message: string, output: string): string {
  return `${message}\n${output}`;
}
