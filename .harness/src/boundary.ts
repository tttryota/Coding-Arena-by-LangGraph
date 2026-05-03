import { existsSync, realpathSync, lstatSync, readFileSync } from "node:fs";
import { resolve, join, dirname } from "node:path";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { GuardError } from "./types.ts";
import type { TaskPlan } from "./types.ts";
import type { SourceLayoutConfig } from "./config.ts";

const execFileAsync = promisify(execFile);

const LOCAL_CMD_TIMEOUT_MS = 5 * 60 * 1000; // 5分

/**
 * パス検証・スコープ解決・ファイル探索を担う。
 * 外部に送るファイルの境界チェックはすべてここを通す。
 */
export class Boundary {
  private projectRoot: string;
  private realRoot: string;
  private sourceLayout: SourceLayoutConfig;
  private fileExtensions: readonly string[];
  private excludeDirs: readonly string[];

  constructor(
    projectRoot: string,
    sourceLayout?: SourceLayoutConfig,
    fileExtensions?: readonly string[],
    excludeDirs?: readonly string[],
  ) {
    this.projectRoot = resolve(projectRoot);
    this.realRoot = realpathSync(this.projectRoot);
    // Phase 5: sourceLayout 駆動。未指定時は Python デフォルト（後方互換）
    this.sourceLayout = sourceLayout ?? {
      sourceDir: "backend/{{category}}",
      testDir: "backend/{{category}}/tests",
      scopePattern: "backend/{{category}}/*",
      additionalAllowedPrefixes: ["docs/reviews/"],
    };
    this.fileExtensions = fileExtensions ?? ["py"];
    this.excludeDirs = excludeDirs ?? ["__pycache__", ".venv"];
  }

  getProjectRoot(): string {
    return this.projectRoot;
  }

  // === パターン解決 ===

  private resolvePattern(pattern: string, scope: string): string {
    const category = this.extractCategory(scope);
    const name = this.extractName(scope);
    return pattern.replaceAll("{{category}}", category).replaceAll("{{name}}", name);
  }

  // === スコープ検証 ===

  validateScope(scope: string): void {
    const parts = scope.split("/");
    if (parts.length !== 2) {
      throw new GuardError(
        `scope は "カテゴリ/名前" の2要素形式で指定してください（例: ingestion/chunk-splitter）。受け取った値: "${scope}"（${parts.length}要素）`,
      );
    }
    for (const segment of parts) {
      this.validatePathSegment(segment);
    }
  }

  extractCategory(featureName: string): string {
    const parts = featureName.split("/");
    if (parts.length !== 2) {
      throw new GuardError(
        `featureName は "カテゴリ/名前" の2要素形式で指定してください（例: ingestion/chunk-splitter）。受け取った値: "${featureName}"（${parts.length}要素）`,
      );
    }
    this.validatePathSegment(parts[0]);
    return parts[0];
  }

  extractName(featureName: string): string {
    const parts = featureName.split("/");
    if (parts.length !== 2) {
      throw new GuardError(
        `featureName は "カテゴリ/名前" の2要素形式で指定してください（例: ingestion/chunk-splitter）。受け取った値: "${featureName}"（${parts.length}要素）`,
      );
    }
    this.validatePathSegment(parts[1]);
    return parts[1];
  }

  // === パス検証 ===

  assertWithinProject(fullPath: string): void {
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
    let current = targetPath;
    while (current !== dirname(current)) {
      current = dirname(current);
      if (existsSync(current)) {
        const realAncestor = realpathSync(current);
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
    if (!this.isReadyLikeStatus(specFm.status)) {
      throw new GuardError(`仕様書が ready ではありません（現在: ${specFm.status ?? "なし"}）`);
    }
    const tcFm = this.readFrontmatter(testCasesFullPath);
    if (!this.isReadyLikeStatus(tcFm.status)) {
      throw new GuardError(`テストケースが ready ではありません（現在: ${tcFm.status ?? "なし"}）`);
    }
  }

  private isReadyLikeStatus(status: string | undefined): boolean {
    return status === "ready" || status === "approved";
  }

  // === ファイル探索（sourceLayout 駆動） ===

  async findSourceFiles(scope: string): Promise<string[]> {
    const sourceDir = this.resolvePattern(this.sourceLayout.sourceDir, scope);
    const testDir = this.resolvePattern(this.sourceLayout.testDir, scope);
    // testDir が sourceDir 配下の場合は重複排除
    const dirs = [join(this.projectRoot, sourceDir)];
    const resolvedTestDir = join(this.projectRoot, testDir);
    if (!resolvedTestDir.startsWith(dirs[0] + "/") && resolvedTestDir !== dirs[0]) {
      dirs.push(resolvedTestDir);
    }
    return this.findFilesInDirs(dirs);
  }

  async findImplementationFiles(scope: string): Promise<string[]> {
    const sourceDir = this.resolvePattern(this.sourceLayout.sourceDir, scope);
    const testDir = this.resolvePattern(this.sourceLayout.testDir, scope);
    const allFiles = await this.findFilesInDirs([join(this.projectRoot, sourceDir)]);
    const resolvedTestDir = join(this.projectRoot, testDir);
    // パス境界を厳密に判定（/tests と /testing を区別）
    const testDirPrefix = resolvedTestDir.endsWith("/") ? resolvedTestDir : resolvedTestDir + "/";
    return allFiles.filter((f) => f !== resolvedTestDir && !f.startsWith(testDirPrefix));
  }

  async findTestFiles(scope: string): Promise<string[]> {
    const testDir = this.resolvePattern(this.sourceLayout.testDir, scope);
    return this.findFilesInDirs([join(this.projectRoot, testDir)]);
  }

  private async findFilesInDirs(dirs: string[]): Promise<string[]> {
    const files: string[] = [];
    // find の -name 条件を拡張子から動的構築
    const nameArgs: string[] = [];
    for (let i = 0; i < this.fileExtensions.length; i++) {
      if (i > 0) nameArgs.push("-o");
      nameArgs.push("-name", `*.${this.fileExtensions[i]}`);
    }
    // 除外ディレクトリ
    const excludeArgs: string[] = [];
    // 除外ディレクトリ: ディレクトリ名の完全一致（/dirname/ パターン）
    for (const excludeDir of this.excludeDirs) {
      excludeArgs.push("-not", "-path", `*/${excludeDir}/*`);
    }

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
        const findArgs = [dir, "-type", "f", "(", ...nameArgs, ")", ...excludeArgs];
        const { stdout } = await execFileAsync("find", findArgs, {
          timeout: LOCAL_CMD_TIMEOUT_MS,
        });
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
    return this.resolvePattern(this.sourceLayout.testDir, scope);
  }

  // === allowedTools（sourceLayout 駆動） ===

  scopeAllowedTools(scope: string): string[] {
    const pattern = this.resolvePattern(this.sourceLayout.scopePattern, scope);
    return ["Read", `Write(${pattern})`, `Edit(${pattern})`];
  }

  implAllowedTools(scope: string): string[] {
    const sourceDir = this.resolvePattern(this.sourceLayout.sourceDir, scope);
    const extGlob = this.fileExtensions.length === 1
      ? `*.${this.fileExtensions[0]}`
      : `*.{${this.fileExtensions.join(",")}}`;
    return ["Read", `Write(${sourceDir}/**/${extGlob})`, `Edit(${sourceDir}/**/${extGlob})`];
  }

  testAllowedTools(scope: string): string[] {
    const testDir = this.resolvePattern(this.sourceLayout.testDir, scope);
    return ["Read", `Write(${testDir}/**)`, `Edit(${testDir}/**)`];
  }

  // === git 操作（sourceLayout 駆動） ===

  private scopeDirs(scope: string): string[] {
    const sourceDir = this.resolvePattern(this.sourceLayout.sourceDir, scope);
    const testDir = this.resolvePattern(this.sourceLayout.testDir, scope);
    // sourceDir と testDir が同じ場合は重複排除
    const dirs = [sourceDir];
    if (testDir !== sourceDir && !testDir.startsWith(sourceDir + "/")) {
      dirs.push(testDir);
    }
    return dirs;
  }

  async stageFiles(scope: string): Promise<void> {
    const dirs = this.scopeDirs(scope);
    try {
      await execFileAsync("git", ["add", ...dirs.map((d) => `${d}/`)], {
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
    const dirs = this.scopeDirs(scope);
    const allowedPrefixes = [
      ...dirs.map((d) => d.endsWith("/") ? d : `${d}/`),
      ...this.sourceLayout.additionalAllowedPrefixes.map((p) => p.endsWith("/") ? p : `${p}/`),
    ];

    const tracked = await this.gitListChangedFiles("git", ["diff", "--name-only", "HEAD"]);
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
      throw new GuardError(`git コマンド失敗: ${cmd} ${args.join(" ")}`);
    }
  }

  async getFileDiff(files: string[]): Promise<string> {
    if (files.length === 0) return "";

    for (const f of files) {
      this.assertWithinProject(resolve(this.projectRoot, f));
    }

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
