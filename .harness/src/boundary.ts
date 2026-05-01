import { existsSync, realpathSync, lstatSync, readFileSync } from "node:fs";
import { resolve, join, dirname } from "node:path";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { GuardError } from "./types.ts";
import type { TaskPlan } from "./types.ts";

const execFileAsync = promisify(execFile);

const LOCAL_CMD_TIMEOUT_MS = 5 * 60 * 1000; // 5分

/**
 * パス検証・スコープ解決・ファイル探索を担う。
 * 外部に送るファイルの境界チェックはすべてここを通す。
 */
export class Boundary {
  private projectRoot: string;
  private realRoot: string;

  constructor(projectRoot: string) {
    this.projectRoot = resolve(projectRoot);
    this.realRoot = realpathSync(this.projectRoot);
  }

  getProjectRoot(): string {
    return this.projectRoot;
  }

  // === スコープ検証 ===

  validateScope(scope: string): void {
    if (!scope.includes("/")) {
      throw new GuardError(
        `scope は "カテゴリ/名前" 形式で指定してください（例: ingestion/chunk-splitter）。受け取った値: "${scope}"`,
      );
    }
    for (const segment of scope.split("/")) {
      this.validatePathSegment(segment);
    }
  }

  extractCategory(featureName: string): string {
    if (!featureName.includes("/")) {
      throw new GuardError(
        `featureName は "カテゴリ/名前" 形式で指定してください（例: ingestion/chunk-splitter）。受け取った値: "${featureName}"`,
      );
    }
    const category = featureName.split("/")[0];
    this.validatePathSegment(category);
    return category;
  }

  extractName(featureName: string): string {
    const name = featureName.split("/").slice(1).join("/");
    this.validatePathSegment(name);
    return name;
  }

  // === パス検証 ===

  assertWithinProject(fullPath: string): void {
    // 存在するパスは直接 realpath、存在しない場合は最も近い既存祖先を realpath
    const realPath = existsSync(fullPath)
      ? realpathSync(fullPath)
      : this.realpathNearestAncestor(fullPath);
    const boundary = this.realRoot.endsWith("/") ? this.realRoot : this.realRoot + "/";
    if (!realPath.startsWith(boundary) && realPath !== this.realRoot) {
      throw new GuardError(
        `パスがプロジェクトルート外を参照しています: ${fullPath} (実体: ${realPath})`,
      );
    }
  }

  private realpathNearestAncestor(targetPath: string): string {
    // 未存在パスの親を遡り、最も近い既存ディレクトリを realpath する
    // 親 symlink がプロジェクト外を指すケースを検出
    let current = targetPath;
    while (current !== dirname(current)) {
      current = dirname(current);
      if (existsSync(current)) {
        const realAncestor = realpathSync(current);
        // 祖先の実パスに、残りの相対パスを付加して返す
        const remainder = targetPath.slice(current.length);
        return realAncestor + remainder;
      }
    }
    return targetPath;
  }

  private validatePathSegment(segment: string): void {
    if (segment.includes("..") || segment.startsWith("/") || segment === "") {
      throw new GuardError(
        `不正なパスセグメント: "${segment}"。パストラバーサルは許可されていません。`,
      );
    }
    // allowedTools 文字列注入防止: CLIメタ文字を拒否
    if (/[,)()*?\\]/.test(segment)) {
      throw new GuardError(
        `不正なパスセグメント: "${segment}"。特殊文字（, ) ( * ? \\）は許可されていません。`,
      );
    }
  }

  // === 実装ガード ===

  implementationGuard(plan: TaskPlan): void {
    if (!plan.specPath) {
      throw new GuardError("計画ファイルに spec が指定されていません。");
    }
    if (!plan.testCasesPath) {
      throw new GuardError("計画ファイルに test_cases が指定されていません。");
    }
    if (!plan.scope) {
      throw new GuardError("計画ファイルに scope が指定されていません。");
    }
    if (plan.scope.startsWith("frontend")) {
      throw new GuardError("frontend スコープの impl フローは Phase 3 で実装予定です。");
    }

    this.validateScope(plan.scope);

    const specFullPath = resolve(this.projectRoot, plan.specPath);
    const testCasesFullPath = resolve(this.projectRoot, plan.testCasesPath);
    this.assertWithinProject(specFullPath);
    this.assertWithinProject(testCasesFullPath);

    if (!plan.targetTestCases || plan.targetTestCases.length === 0) {
      throw new GuardError("対象テストケースが指定されていません。");
    }

    if (!existsSync(specFullPath)) {
      throw new GuardError(`仕様書が存在しません: ${plan.specPath}`);
    }
    if (!existsSync(testCasesFullPath)) {
      throw new GuardError(`テストケースが存在しません: ${plan.testCasesPath}`);
    }

    const specFm = this.readFrontmatter(specFullPath);
    if (specFm.status !== "approved") {
      throw new GuardError(`仕様書が未承認です（現在: ${specFm.status ?? "なし"}）`);
    }
    const tcFm = this.readFrontmatter(testCasesFullPath);
    if (tcFm.status !== "approved") {
      throw new GuardError(`テストケースが未承認です（現在: ${tcFm.status ?? "なし"}）`);
    }
  }

  // === ファイル探索 ===

  async findPythonFiles(scope: string): Promise<string[]> {
    const category = scope.includes("/") ? scope.split("/")[0] : scope;
    return this.findPythonFilesInDirs([
      join(this.projectRoot, "backend", category),
      join(this.projectRoot, "backend", category, "tests"),
    ]);
  }

  async findImplementationFiles(scope: string): Promise<string[]> {
    const category = scope.includes("/") ? scope.split("/")[0] : scope;
    const dir = join(this.projectRoot, "backend", category);
    const allFiles = await this.findPythonFilesInDirs([dir]);
    return allFiles.filter((f) => !f.includes("/tests/"));
  }

  async findTestFiles(scope: string): Promise<string[]> {
    const category = scope.includes("/") ? scope.split("/")[0] : scope;
    return this.findPythonFilesInDirs([
      join(this.projectRoot, "backend", category, "tests"),
    ]);
  }

  private async findPythonFilesInDirs(dirs: string[]): Promise<string[]> {
    const files: string[] = [];
    for (const dir of dirs) {
      if (!existsSync(dir)) continue;
      if (lstatSync(dir).isSymbolicLink()) {
        const realDir = realpathSync(dir);
        const boundary = this.realRoot.endsWith("/") ? this.realRoot : this.realRoot + "/";
        if (!realDir.startsWith(boundary)) {
          throw new GuardError(
            `プロジェクト外を参照する symlink ディレクトリが検出されました: ${dir} -> ${realDir}`,
          );
        }
      }
      try {
        const { stdout } = await execFileAsync("find", [
          dir, "-name", "*.py", "-type", "f", "-not", "-path", "*__pycache__*",
        ], { timeout: LOCAL_CMD_TIMEOUT_MS });
        for (const f of stdout.split("\n").filter(Boolean)) {
          if (this.isFileWithinProject(f)) {
            files.push(f);
          }
        }
      } catch (error: unknown) {
        const execError = error as { code?: string; stderr?: string };
        if (execError.code === "ENOENT") {
          throw new GuardError("find コマンドが見つかりません。");
        }
        throw new GuardError(
          `${dir} のファイル探索に失敗しました。権限やディレクトリ構造を確認してください。\n${execError.stderr ?? ""}`,
        );
      }
    }
    return files;
  }

  testPathForScope(scope: string): string {
    const category = scope.includes("/") ? scope.split("/")[0] : scope;
    return join("backend", category, "tests");
  }

  /**
   * scope に対応する allowedTools のパス制限パターンを生成。
   * Claude の --allowedTools で使用。
   */
  scopeAllowedTools(scope: string): string[] {
    const category = scope.includes("/") ? scope.split("/")[0] : scope;
    return [
      "Read",
      `Write(backend/${category}/*)`,
      `Edit(backend/${category}/*)`,
    ];
  }

  // === git 操作 ===

  async stageFiles(scope: string): Promise<void> {
    const category = scope.includes("/") ? scope.split("/")[0] : scope;
    try {
      await execFileAsync("git", ["add", `backend/${category}/`], {
        cwd: this.projectRoot, timeout: 30_000,
      });
    } catch (error: unknown) {
      const execError = error as { code?: string };
      if (execError.code === "ENOENT") {
        throw new GuardError("git が見つかりません。");
      }
      throw new GuardError("git add の実行に失敗しました。");
    }
  }

  async getCurrentCommitHash(): Promise<string> {
    try {
      const { stdout } = await execFileAsync("git", ["rev-parse", "HEAD"], {
        cwd: this.projectRoot, timeout: 30_000,
      });
      return stdout.trim();
    } catch {
      return "";
    }
  }

  async countDiffLines(): Promise<number> {
    // 未コミットの変更（ステージ済み + 未ステージ）を数える
    // fail-closed: git 失敗時は 0 ではなくエラーにする
    try {
      const { stdout } = await execFileAsync(
        "git", ["diff", "HEAD", "--stat"],
        { cwd: this.projectRoot, timeout: 30_000 },
      );
      const pattern = /(\d+) insertion|(\d+) deletion/g;
      let total = 0;
      let m: RegExpExecArray | null;
      while ((m = pattern.exec(stdout)) !== null) {
        total += parseInt(m[1] ?? m[2], 10);
      }
      return total;
    } catch (error: unknown) {
      const execError = error as { code?: string };
      if (execError.code === "ENOENT") {
        throw new GuardError("git が見つかりません。");
      }
      throw new GuardError("git diff の実行に失敗しました。差分サイズを検証できません。");
    }
  }

  async verifyChangedFilesWithinScope(scope: string): Promise<void> {
    const category = scope.includes("/") ? scope.split("/")[0] : scope;
    const allowedPrefixes = [
      `backend/${category}/`,
      `docs/reviews/`,
    ];

    // 変更済みファイル（ステージ済み + 未ステージ）
    const tracked = await this.gitListChangedFiles("git", ["diff", "--name-only", "HEAD"]);
    // 未追跡の新規ファイル
    const untracked = await this.gitListChangedFiles("git", ["ls-files", "--others", "--exclude-standard"]);
    const allChanged = [...tracked, ...untracked];

    for (const file of allChanged) {
      const inScope = allowedPrefixes.some((prefix) => file.startsWith(prefix));
      if (!inScope) {
        throw new GuardError(
          `スコープ外のファイルが変更されています: ${file}\n許可されたプレフィクス: ${allowedPrefixes.join(", ")}`,
        );
      }
    }
  }

  private async gitListChangedFiles(cmd: string, args: string[]): Promise<string[]> {
    try {
      const { stdout } = await execFileAsync(cmd, args, { cwd: this.projectRoot, timeout: LOCAL_CMD_TIMEOUT_MS });
      return stdout.split("\n").filter(Boolean);
    } catch (error: unknown) {
      const execError = error as { code?: string };
      if (execError.code === "ENOENT") {
        throw new GuardError("git が見つかりません。");
      }
      // git コマンド失敗は fail-closed: 空ではなくエラーとする
      throw new GuardError(`git コマンド失敗: ${cmd} ${args.join(" ")}`);
    }
  }

  determineCriteriaPaths(scope: string): string[] {
    const harnessDir = join(this.projectRoot, ".harness");
    const paths = [join(harnessDir, "review-criteria-common.md")];
    if (scope.startsWith("frontend")) {
      paths.push(join(harnessDir, "review-criteria-frontend.md"));
    } else {
      paths.push(join(harnessDir, "review-criteria-backend.md"));
    }
    return paths;
  }

  async getFileDiff(files: string[]): Promise<string> {
    if (files.length === 0) return "";

    // 各ファイルの境界チェック
    for (const f of files) {
      this.assertWithinProject(resolve(this.projectRoot, f));
    }

    // ステージ済みファイルに対するワーキングツリーの差分を取得
    // （stageFiles で git add 済みなので、修正箇所のみが差分として出る）
    try {
      const { stdout } = await execFileAsync(
        "git", ["diff", "--", ...files],
        { cwd: this.projectRoot, maxBuffer: 10 * 1024 * 1024, timeout: LOCAL_CMD_TIMEOUT_MS },
      );
      return stdout;
    } catch {
      return "(git diff 取得失敗)";
    }
  }

  // === frontmatter パース ===

  readFrontmatter(filePath: string): Record<string, string> {
    const content = readFileSync(filePath, "utf-8").replace(/\r\n/g, "\n");
    const match = /^---\n([\s\S]*?)\n---/.exec(content);
    if (!match) return {};

    const result: Record<string, string> = {};
    for (const line of match[1].split("\n")) {
      const colonIndex = line.indexOf(":");
      if (colonIndex === -1) continue;
      const key = line.slice(0, colonIndex).trim();
      const rawValue = line.slice(colonIndex + 1).trim();
      const value = rawValue.replace(/^["']|["']$/g, "");
      if (key && value) {
        result[key] = value;
      }
    }
    return result;
  }

  parsePlanFile(planPath: string): TaskPlan {
    const fullPath = resolve(this.projectRoot, planPath);
    this.assertWithinProject(fullPath);
    if (!existsSync(fullPath)) {
      throw new GuardError(`計画ファイルが存在しません: ${planPath}`);
    }
    // CRLF 正規化 + 見出し末尾スペース除去
    const content = readFileSync(fullPath, "utf-8")
      .replace(/\r\n/g, "\n")
      .replace(/^(## .+?) +$/gm, "$1");
    const frontmatter = this.readFrontmatter(fullPath);

    const extract = (heading: string): string | undefined => {
      const re = new RegExp(`## ${heading}\\n([\\s\\S]*?)(?=\\n## |$)`);
      return re.exec(content)?.[1];
    };

    const parseList = (text: string | undefined): string[] =>
      (text ?? "")
        .split("\n")
        .map((line) => line.replace(/^[-\d.]+\s*/, "").trim())
        .filter(Boolean);

    return {
      scope: frontmatter.scope ?? "",
      specPath: frontmatter.spec ?? "",
      testCasesPath: frontmatter.test_cases ?? "",
      description: extract("今回やること")?.trim() ?? "",
      targetTestCases: parseList(extract("対象テストケース")),
      exclusions: parseList(extract("やらないこと")),
      completionCriteria: parseList(extract("完了条件")),
      designDecisions: parseList(extract("設計判断")),
    };
  }

  // === 内部ヘルパー ===

  private isFileWithinProject(filePath: string): boolean {
    try {
      if (lstatSync(filePath).isSymbolicLink()) {
        const realPath = realpathSync(filePath);
        const boundary = this.realRoot.endsWith("/") ? this.realRoot : this.realRoot + "/";
        return realPath.startsWith(boundary);
      }
      return true;
    } catch {
      return false;
    }
  }
}
