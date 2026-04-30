import { execFile } from "node:child_process";
import { promisify } from "node:util";
import type { HarnessLogger } from "./logger.ts";
import { DriftError, ESCALATION_LEVEL, EVENT } from "./types.ts";
import type { LintViolation } from "./types.ts";

const execFileAsync = promisify(execFile);

const MAX_LINT_RETRIES = 3;

export class LintGuard {
  private logger: HarnessLogger;
  private projectRoot: string;

  constructor(logger: HarnessLogger, projectRoot: string) {
    this.logger = logger;
    this.projectRoot = projectRoot;
  }

  async check(targetFiles: string[]): Promise<void> {
    for (let attempt = 1; attempt <= MAX_LINT_RETRIES; attempt++) {
      const formatOk = await this.runRuffFormat(targetFiles);
      if (!formatOk) {
        throw new Error("ruff format が失敗しました。設定を確認してください。");
      }

      const ruffViolations = await this.runRuffCheck(targetFiles);
      const mypyViolations = await this.runMypy(targetFiles);
      const allViolations = [...ruffViolations, ...mypyViolations];

      if (allViolations.length === 0) {
        this.logger.log(EVENT.LINT_PASSED, { attempt });
        return;
      }

      this.logger.log(EVENT.LINT_VIOLATIONS, {
        attempt,
        count: allViolations.length,
        violations: allViolations,
      });

      if (attempt < MAX_LINT_RETRIES) {
        await this.autoFix(targetFiles);
      }
    }

    throw new DriftError(
      ESCALATION_LEVEL.LEVEL_1,
      "lint_retry",
      `リンター違反が ${MAX_LINT_RETRIES} 回の修正後も残っています`,
    );
  }

  async runRuffCheck(targetFiles: string[]): Promise<LintViolation[]> {
    const configPath = `${this.projectRoot}/backend/pyproject.toml`;
    const result = await this.exec("ruff", [
      "check",
      "--config",
      configPath,
      "--output-format",
      "json",
      ...targetFiles,
    ]);

    this.logger.logCommand("ruff", ["check", ...targetFiles], result);

    if (result.exitCode === 0) return [];

    try {
      const parsed = JSON.parse(result.stdout) as Array<{
        filename: string;
        location: { row: number };
        message: string;
        code: string;
      }>;
      return parsed.map((v) => ({
        tool: "ruff_check",
        file: v.filename,
        line: v.location.row,
        message: `${v.code}: ${v.message}`,
      }));
    } catch {
      return [
        {
          tool: "ruff_check",
          file: "",
          line: 0,
          message: result.stderr || result.stdout,
        },
      ];
    }
  }

  async runRuffFormat(targetFiles: string[]): Promise<boolean> {
    const configPath = `${this.projectRoot}/backend/pyproject.toml`;
    const result = await this.exec("ruff", [
      "format",
      "--config",
      configPath,
      ...targetFiles,
    ]);

    this.logger.logCommand("ruff", ["format", ...targetFiles], result);
    return result.exitCode === 0;
  }

  async runMypy(targetFiles: string[]): Promise<LintViolation[]> {
    const configPath = `${this.projectRoot}/backend/pyproject.toml`;
    const result = await this.exec("mypy", [
      "--config-file",
      configPath,
      "--strict",
      ...targetFiles,
    ]);

    this.logger.logCommand("mypy", ["--strict", ...targetFiles], result);

    if (result.exitCode === 0) return [];

    const violations: LintViolation[] = [];
    for (const line of result.stdout.split("\n")) {
      const match = /^(.+):(\d+): error: (.+)$/.exec(line);
      if (match) {
        violations.push({
          tool: "mypy",
          file: match[1],
          line: parseInt(match[2], 10),
          message: match[3],
        });
      }
    }

    // 非ゼロ終了なのに violations が空 = 設定エラーやクラッシュ
    if (violations.length === 0 && result.exitCode !== 0) {
      throw new Error(
        `mypy が非ゼロで終了しましたが、型エラーを検出できませんでした。設定エラーの可能性があります。\nstdout: ${result.stdout}\nstderr: ${result.stderr}`,
      );
    }

    return violations;
  }

  private async autoFix(targetFiles: string[]): Promise<void> {
    const configPath = `${this.projectRoot}/backend/pyproject.toml`;
    await this.exec("ruff", [
      "check",
      "--fix",
      "--config",
      configPath,
      ...targetFiles,
    ]);
  }

  private async exec(
    command: string,
    args: string[],
  ): Promise<{ stdout: string; stderr: string; exitCode: number }> {
    try {
      const { stdout, stderr } = await execFileAsync(command, args, {
        cwd: this.projectRoot,
        maxBuffer: 10 * 1024 * 1024,
      });
      return { stdout, stderr, exitCode: 0 };
    } catch (error: unknown) {
      const execError = error as {
        stdout?: string;
        stderr?: string;
        code?: number | string;
      };
      // ENOENT: コマンドが見つからない場合は即座にエラー
      if (execError.code === "ENOENT") {
        throw new Error(`${command} が見つかりません。インストールしてください。`);
      }
      return {
        stdout: execError.stdout ?? "",
        stderr: execError.stderr ?? "",
        exitCode: typeof execError.code === "number" ? execError.code : 1,
      };
    }
  }
}
