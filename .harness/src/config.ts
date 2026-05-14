import { readFileSync, existsSync } from "node:fs";
import { join, relative, resolve } from "node:path";
import { parse as parseYaml } from "yaml";
import { HarnessError, GuardError } from "./types.ts";
import { LINT_REGISTRY, TEST_REGISTRY } from "./tool-adapter.ts";
import { FLOW_STEP } from "./steps.ts";
import type { FlowMode, FlowStep } from "./steps.ts";

// === Runner 型（変更なし） ===

export type RunnerConfig =
  | { type: "claude"; timeoutMs?: number }
  | { type: "codex"; sandbox?: string; timeoutMs?: number }
  | {
      type: "generic";
      command: string;
      args: string[];
      promptFlag?: string;
      timeoutMs?: number;
    };

// === SourceLayout ===

export type UserSourceLayoutConfig = {
  sourceDir?: string;
  testDir?: string;
  scopePattern?: string;
  additionalAllowedPrefixes?: string[];
};

export type UserStorybookConfig = {
  renderCommand?: string[];
  smokeCommand?: string[];
};

export type UserClaudeStepOverrideConfig = {
  agent?: string;
  skillBundles?: string[];
  mcpBundles?: string[];
};

export type UserProfileClaudeConfig = {
  defaultAgent?: string;
  defaultSkillBundles?: string[];
  defaultMcpBundles?: string[];
  stepOverrides?: Partial<Record<FlowStep, UserClaudeStepOverrideConfig>>;
};

export type SourceLayoutConfig = {
  sourceDir: string;
  testDir: string;
  scopePattern: string;
  additionalAllowedPrefixes: string[];
};

export type ClaudeStepOverrideConfig = {
  agent?: string;
  skillBundles: string[];
  mcpBundles: string[];
};

export type ProfileClaudeConfig = {
  defaultAgent?: string;
  defaultSkillBundles: string[];
  defaultMcpBundles: string[];
  stepOverrides: Partial<Record<FlowStep, ClaudeStepOverrideConfig>>;
};

export type UserClaudeConfig = {
  skillBundles?: Record<string, string[]>;
  mcpBundles?: Record<string, string[]>;
};

export type ResolvedClaudeConfig = {
  skillBundles: Record<string, string[]>;
  mcpBundles: Record<string, string[]>;
};

// === Profile ===

export type UserProfileConfig = {
  lint?: string[];
  test?: string;
  sourceLayout?: UserSourceLayoutConfig;
  storybook?: UserStorybookConfig;
  exec?: string | string[];
  toolRoot?: string;
  reviewCriteria?: string[];
  criteriaPreset?: "backend" | "frontend";
  claude?: UserProfileClaudeConfig;
};

export type StorybookConfig = {
  renderCommand: string[];
  smokeCommand: string[];
};

export type ResolvedProfileConfig = {
  lint: string[];
  test: string;
  sourceLayout: SourceLayoutConfig;
  storybook?: StorybookConfig;
  exec: string[];
  toolRoot: string;
  reviewCriteria: string[];
  criteriaPreset: "backend" | "frontend" | undefined;
  claude?: ProfileClaudeConfig;
};

// === Config ===

export type HarnessUserConfig = {
  profiles?: Record<string, UserProfileConfig>;
  runners?: Record<string, RunnerConfig>;
  flow?: FlowMode;
  steps?: Partial<Record<FlowStep, string>>;
  fallbackRunner?: string;
  templates?: Record<string, string | null>;
  claude?: UserClaudeConfig;
};

export type ResolvedConfig = {
  profiles: Record<string, ResolvedProfileConfig>;
  runners: Record<string, RunnerConfig>;
  flow: FlowMode;
  steps: Partial<Record<FlowStep, string>>;
  fallbackRunner: string;
  templates: Record<string, string | null>;
  claude: ResolvedClaudeConfig;
};

// 旧 HarnessConfig との互換エイリアス（既存 import を壊さないため）
export type HarnessConfig = ResolvedConfig;

// === 定数 ===

const PREFERRED_CONFIG_PATH = ".harness/harness.yml";
const LEGACY_CONFIG_PATH = ".harness.yml";
const CONFIG_FILENAMES = [
  PREFERRED_CONFIG_PATH,
  ".harness/harness.yaml",
  LEGACY_CONFIG_PATH,
  ".harness.yaml",
];

const DEFAULT_STEPS: Partial<Record<FlowStep, string>> = {
  test_generate: "claude",
  test_self_quality: "claude",
  test_external_review: "claude",
  impl_generate: "claude",
  impl_self_criteria: "claude",
  impl_self_quality: "claude",
  impl_external_review: "claude",
  lint_fix: "claude",
  apply_fixes: "claude",
  judgment_summary: "claude",
  judge_minor: "claude",
  spec_generate: "claude",
  test_case_generate: "claude",
  component_generate: "claude",
  component_self_review: "claude",
  page_generate: "claude",
  page_review_design: "claude",
  page_review_behavior: "claude",
  page_review_code: "claude",
  page_browser_verify: "claude",
};

// === loadConfig ===

export function loadConfig(projectRoot: string): ResolvedConfig {
  let userConfig: HarnessUserConfig = {};
  const configPath = findConfigPath(projectRoot);

  if (configPath) {
    const raw = readFileSync(configPath, "utf-8");
    const parsed = parseYaml(raw);
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
      userConfig = parsed as HarnessUserConfig;
    } else {
      throw new GuardError(
        `設定ファイルの形式が不正です: ${relativeConfigPath(projectRoot, configPath)}。YAML オブジェクトを記述してください。`,
      );
    }
  }

  // 型ガード: トップレベルフィールドの簡易検証
  validateUserConfigShape(userConfig);

  // profiles がない場合は Python デフォルトに移行
  const migrated = requireProfiles(userConfig);

  const runners = migrated.runners ?? { claude: { type: "claude" } };
  const runnerNames = Object.keys(runners);
  const defaultRunner = migrated.fallbackRunner ?? runnerNames[0] ?? "claude";

  // ユーザー指定の steps に未知 runner があればエラー（typo 検出）
  if (migrated.steps) {
    for (const [step, runner] of Object.entries(migrated.steps)) {
      if (runner && !runners[runner]) {
        throw new GuardError(
          `steps.${step} に指定された runner "${runner}" が runners に存在しません。利用可能: ${runnerNames.join(", ")}`,
        );
      }
    }
  }

  // デフォルト steps: runners に "claude" があれば claude、なければ先頭 runner
  const stepDefault = runners["claude"] ? "claude" : runnerNames[0] ?? "claude";
  const defaultSteps: Partial<Record<FlowStep, string>> = {};
  for (const [key, val] of Object.entries(DEFAULT_STEPS)) {
    // デフォルト runner が利用不可なら stepDefault に差し替え
    defaultSteps[key as FlowStep] = val && runners[val] ? val : stepDefault;
  }
  const mergedSteps = { ...defaultSteps, ...migrated.steps };

  const resolved: ResolvedConfig = {
    profiles: resolveProfiles(migrated.profiles ?? {}, projectRoot),
    runners,
    flow: migrated.flow ?? "full",
    steps: mergedSteps,
    fallbackRunner: defaultRunner,
    templates: migrated.templates ?? {},
    claude: resolveClaudeConfig(migrated.claude),
  };

  validateConfig(resolved);
  return resolved;
}

// === 入力スキーマ検証 ===

function validateUserConfigShape(config: HarnessUserConfig): void {
  // profiles の各 profile.lint が配列であること
  if (config.profiles) {
    if (typeof config.profiles !== "object" || Array.isArray(config.profiles)) {
      throw new GuardError("profiles はオブジェクト形式で指定してください。");
    }
    for (const [name, profile] of Object.entries(config.profiles)) {
      if (!profile || typeof profile !== "object" || Array.isArray(profile)) {
        throw new GuardError(`profile "${name}" はオブジェクト形式で指定してください（配列不可）。`);
      }
      if (profile.lint !== undefined && !Array.isArray(profile.lint)) {
        throw new GuardError(
          `profile "${name}".lint は配列で指定してください。例: lint: [ruff, mypy]`,
        );
      }
      if (profile.lint !== undefined) {
        for (const t of profile.lint) {
          if (typeof t !== "string") {
            throw new GuardError(`profile "${name}".lint の各要素は文字列である必要があります。`);
          }
        }
      }
      if (profile.test !== undefined && typeof profile.test !== "string") {
        throw new GuardError(
          `profile "${name}".test は文字列で指定してください。例: test: pytest`,
        );
      }
      if (profile.reviewCriteria !== undefined) {
        if (!Array.isArray(profile.reviewCriteria)) {
          throw new GuardError(`profile "${name}".reviewCriteria は配列で指定してください。`);
        }
        for (const c of profile.reviewCriteria) {
          if (typeof c !== "string") {
            throw new GuardError(`profile "${name}".reviewCriteria の各要素は文字列である必要があります。`);
          }
        }
      }
      if (profile.sourceLayout !== undefined) {
        if (typeof profile.sourceLayout !== "object" || Array.isArray(profile.sourceLayout)) {
          throw new GuardError(`profile "${name}".sourceLayout はオブジェクト形式で指定してください。`);
        }
        const sl = profile.sourceLayout;
        if (sl.sourceDir !== undefined && typeof sl.sourceDir !== "string") {
          throw new GuardError(`profile "${name}".sourceLayout.sourceDir は文字列である必要があります。`);
        }
        if (sl.testDir !== undefined && typeof sl.testDir !== "string") {
          throw new GuardError(`profile "${name}".sourceLayout.testDir は文字列である必要があります。`);
        }
        if (sl.scopePattern !== undefined && typeof sl.scopePattern !== "string") {
          throw new GuardError(`profile "${name}".sourceLayout.scopePattern は文字列である必要があります。`);
        }
        if (sl.additionalAllowedPrefixes !== undefined) {
          if (!Array.isArray(sl.additionalAllowedPrefixes)) {
            throw new GuardError(`profile "${name}".sourceLayout.additionalAllowedPrefixes は配列で指定してください。`);
          }
          for (const p of sl.additionalAllowedPrefixes) {
            if (typeof p !== "string") {
              throw new GuardError(`profile "${name}".sourceLayout.additionalAllowedPrefixes の各要素は文字列である必要があります。`);
            }
          }
        }
      }
      if (profile.storybook !== undefined) {
        if (typeof profile.storybook !== "object" || Array.isArray(profile.storybook)) {
          throw new GuardError(`profile "${name}".storybook はオブジェクト形式で指定してください。`);
        }
        const sb = profile.storybook;
        if (sb.renderCommand !== undefined) {
          validateStringArrayField(sb.renderCommand, `profile "${name}".storybook.renderCommand`);
        }
        if (sb.smokeCommand !== undefined) {
          validateStringArrayField(sb.smokeCommand, `profile "${name}".storybook.smokeCommand`);
        }
      }
      if (profile.criteriaPreset !== undefined) {
        if (profile.criteriaPreset !== "backend" && profile.criteriaPreset !== "frontend") {
          throw new GuardError(
            `profile "${name}".criteriaPreset は "backend" または "frontend" で指定してください。受け取った値: "${profile.criteriaPreset}"`,
          );
        }
      }
      if (profile.toolRoot !== undefined && typeof profile.toolRoot !== "string") {
        throw new GuardError(`profile "${name}".toolRoot は文字列である必要があります。`);
      }
      if (profile.claude !== undefined) {
        validateProfileClaudeConfig(profile.claude, `profile "${name}".claude`);
      }
    }
  }

  // fallbackRunner / templates / steps の型検証
  if (config.fallbackRunner !== undefined && typeof config.fallbackRunner !== "string") {
    throw new GuardError("fallbackRunner は文字列で指定してください。");
  }
  if (config.templates !== undefined) {
    if (typeof config.templates !== "object" || Array.isArray(config.templates)) {
      throw new GuardError("templates はオブジェクト形式で指定してください。");
    }
  }
  if (config.claude !== undefined) {
    validateBundleRecord(config.claude.skillBundles, "claude.skillBundles");
    validateBundleRecord(config.claude.mcpBundles, "claude.mcpBundles");
  }
  if (config.steps !== undefined) {
    if (typeof config.steps !== "object" || Array.isArray(config.steps)) {
      throw new GuardError("steps はオブジェクト形式で指定してください。");
    }
  }

  // flow の enum 検証
  if (config.flow !== undefined && config.flow !== "full" && config.flow !== "light") {
    throw new GuardError(
      `flow は "full" または "light" で指定してください。受け取った値: "${config.flow}"`,
    );
  }

  // runners の shape 検証
  if (config.runners !== undefined) {
    if (typeof config.runners !== "object" || Array.isArray(config.runners)) {
      throw new GuardError("runners はオブジェクト形式で指定してください。");
    }
    for (const [name, runner] of Object.entries(config.runners)) {
      if (!runner || typeof runner !== "object" || !("type" in runner)) {
        throw new GuardError(
          `runner "${name}" には type フィールドが必要です。`,
        );
      }
      const r = runner as Record<string, unknown>;
      const validTypes = ["claude", "codex", "generic"];
      if (!validTypes.includes(r.type as string)) {
        throw new GuardError(
          `runner "${name}" の type "${r.type}" は不正です。利用可能: ${validTypes.join(", ")}`,
        );
      }
      if (r.type === "generic") {
        if (typeof r.command !== "string" || !r.command) {
          throw new GuardError(
            `runner "${name}" (type: generic) には command (文字列) が必要です。`,
          );
        }
        if (!Array.isArray(r.args)) {
          throw new GuardError(
            `runner "${name}" (type: generic) には args (文字列配列) が必要です。`,
          );
        }
        for (const arg of r.args as unknown[]) {
          if (typeof arg !== "string") {
            throw new GuardError(
              `runner "${name}" (type: generic) の args の各要素は文字列である必要があります。`,
            );
          }
        }
        if (r.promptFlag !== undefined && typeof r.promptFlag !== "string") {
          throw new GuardError(
            `runner "${name}" (type: generic) の promptFlag は文字列である必要があります。`,
          );
        }
      }
      if (r.timeoutMs !== undefined && (typeof r.timeoutMs !== "number" || r.timeoutMs <= 0)) {
        throw new GuardError(
          `runner "${name}" の timeoutMs は正の数値である必要があります。`,
        );
      }
      if (r.type === "codex" && r.sandbox !== undefined && typeof r.sandbox !== "string") {
        throw new GuardError(
          `runner "${name}" (type: codex) の sandbox は文字列である必要があります。`,
        );
      }
    }
  }
}

// === profiles 検証 ===

function requireProfiles(config: HarnessUserConfig): HarnessUserConfig {
  if (config.profiles && Object.keys(config.profiles).length > 0) {
    return config;
  }
  throw new GuardError(
    `profiles が定義されていません。${configLocationMessage()} に profiles を追加してください。\n\`tdd-harness init\` でセットアップガイドを表示できます。`,
  );
}

// === Profile 解決 ===

function resolveProfiles(
  profiles: Record<string, UserProfileConfig>,
  projectRoot: string,
): Record<string, ResolvedProfileConfig> {
  const result: Record<string, ResolvedProfileConfig> = {};
  for (const [name, user] of Object.entries(profiles)) {
    result[name] = resolveOneProfile(user, projectRoot);
  }
  return result;
}

function resolveOneProfile(
  user: UserProfileConfig,
  projectRoot: string,
): ResolvedProfileConfig {
  // 明示指定されたツール名を先に検証
  if (user.lint !== undefined) {
    for (const t of user.lint) {
      if (!LINT_REGISTRY[t]) {
        throw new GuardError(
          `未知の lint ツール "${t}"。利用可能: ${Object.keys(LINT_REGISTRY).join(", ")}`,
        );
      }
    }
  }
  if (user.test !== undefined && !TEST_REGISTRY[user.test]) {
    throw new GuardError(
      `未知のテストランナー "${user.test}"。利用可能: ${Object.keys(TEST_REGISTRY).join(", ")}`,
    );
  }

  // デフォルト適用
  const hasExplicitLint = user.lint !== undefined;
  const hasExplicitTest = user.test !== undefined;

  let lint: string[];
  let test: string;

  if (hasExplicitLint && hasExplicitTest) {
    lint = user.lint!;
    test = user.test!;
  } else if (!hasExplicitLint && !hasExplicitTest) {
    lint = ["ruff", "mypy"];
    test = "pytest";
  } else if (hasExplicitTest && !hasExplicitLint) {
    test = user.test!;
    const testRuntime = TEST_REGISTRY[test]?.runtime;
    if (testRuntime === "python") {
      lint = ["ruff", "mypy"];
    } else {
      throw new GuardError(
        `lint が未指定ですが、test "${test}" (runtime: ${testRuntime}) に対するデフォルト lint は runtime が一致しません。lint を明示指定してください。`,
      );
    }
  } else {
    lint = user.lint!;
    const lintRuntime = LINT_REGISTRY[lint[0]]?.runtime;
    if (lintRuntime === "python") {
      test = "pytest";
    } else {
      throw new GuardError(
        `test が未指定ですが、lint の runtime (${lintRuntime}) に対するデフォルト test は runtime が一致しません。test を明示指定してください。`,
      );
    }
  }
  const rawToolRoot = user.toolRoot ?? ".";
  const toolRoot = resolve(projectRoot, rawToolRoot);
  const exec = normalizeExec(user.exec);
  const reviewCriteria = user.reviewCriteria ?? [];
  const storybook = user.storybook
    ? {
        renderCommand: [...(user.storybook.renderCommand ?? [])],
        smokeCommand: [...(user.storybook.smokeCommand ?? [])],
      }
    : undefined;

  const userLayout = user.sourceLayout;
  const sourceLayout: SourceLayoutConfig = {
    sourceDir: userLayout?.sourceDir ?? "backend/{{category}}",
    testDir: userLayout?.testDir ?? "backend/{{category}}/tests",
    scopePattern:
      userLayout?.scopePattern ??
      `${userLayout?.sourceDir ?? "backend/{{category}}"}/*`,
    additionalAllowedPrefixes:
      userLayout?.additionalAllowedPrefixes ?? ["docs/reviews/"],
  };

  return {
    lint,
    test,
    sourceLayout,
    storybook,
    exec,
    toolRoot,
    reviewCriteria,
    criteriaPreset: user.criteriaPreset,
    claude: resolveProfileClaudeConfig(user.claude),
  };
}

// === exec 正規化 ===

function normalizeExec(raw: unknown): string[] {
  if (raw === undefined || raw === null) return [];
  if (Array.isArray(raw)) {
    for (const elem of raw) {
      if (typeof elem !== "string") {
        throw new HarnessError(
          `exec の要素は文字列である必要があります。不正な要素: ${JSON.stringify(elem)}`,
        );
      }
    }
    const result = raw as string[];
    for (const elem of result) {
      validateExecElement(elem);
    }
    return result;
  }
  if (typeof raw === "string") {
    validateExecElement(raw);
    return [raw];
  }
  throw new HarnessError(
    "exec は配列で指定してください。例: exec: [poetry, run]",
  );
}

function validateExecElement(elem: string): void {
  if (elem.length === 0) {
    throw new HarnessError("exec の要素に空文字列は指定できません。");
  }
  if (elem !== elem.trim()) {
    throw new HarnessError(
      `exec の要素に前後の空白を含む文字列は指定できません: "${elem}"`,
    );
  }
  // 内部空白は許可（execFile は引数を個別に渡すため安全。Windows の "Program Files" 等に対応）
}

// === Validation ===

function validateConfig(config: ResolvedConfig): void {
  const profileNames = Object.keys(config.profiles);
  if (profileNames.length === 0) {
    throw new GuardError(
      `profiles が定義されていません。${configLocationMessage()} に profiles を追加してください。`,
    );
  }

  for (const [name, profile] of Object.entries(config.profiles)) {
    validateProfile(name, profile, config.claude);
  }

  // runners
  const runnerNames = Object.keys(config.runners);
  if (runnerNames.length === 0) {
    throw new GuardError("runners が定義されていません。");
  }
  if (!config.runners[config.fallbackRunner]) {
    throw new GuardError(
      `fallbackRunner "${config.fallbackRunner}" が runners に存在しません。利用可能: ${runnerNames.join(", ")}`,
    );
  }
  const validStepKeys = new Set(Object.values(FLOW_STEP));
  for (const [step, runner] of Object.entries(config.steps)) {
    if (!validStepKeys.has(step as FlowStep)) {
      throw new GuardError(
        `steps に未知のキー "${step}" が指定されています。利用可能: ${[...validStepKeys].join(", ")}`,
      );
    }
    if (runner && !config.runners[runner]) {
      throw new GuardError(
        `steps.${step} に指定された runner "${runner}" が runners に存在しません。利用可能: ${runnerNames.join(", ")}`,
      );
    }
  }
}

function validateProfile(
  name: string,
  profile: ResolvedProfileConfig,
  rootClaudeConfig: ResolvedClaudeConfig,
): void {
  // lint 非空
  if (profile.lint.length === 0) {
    throw new GuardError(
      `profile "${name}": lint ツールが指定されていません。`,
    );
  }

  // lint ツール存在確認
  for (const tool of profile.lint) {
    if (!LINT_REGISTRY[tool]) {
      throw new GuardError(
        `profile "${name}": 未知の lint ツール "${tool}"。利用可能: ${Object.keys(LINT_REGISTRY).join(", ")}`,
      );
    }
  }

  // mixed runtime 禁止
  const runtimes = new Set(
    profile.lint.map((t) => LINT_REGISTRY[t].runtime),
  );
  if (runtimes.size > 1) {
    throw new GuardError(
      `profile "${name}": 異なる runtime の lint ツールを混在させることはできません（検出: ${[...runtimes].join(", ")}）。profile を分けてください。`,
    );
  }

  // test ツール存在確認
  if (!TEST_REGISTRY[profile.test]) {
    throw new GuardError(
      `profile "${name}": 未知のテストランナー "${profile.test}"。利用可能: ${Object.keys(TEST_REGISTRY).join(", ")}`,
    );
  }

  // test runtime と lint runtime の一致
  const lintRuntime = [...runtimes][0];
  const testRuntime = TEST_REGISTRY[profile.test].runtime;
  if (lintRuntime && testRuntime !== lintRuntime) {
    throw new GuardError(
      `profile "${name}": lint runtime (${lintRuntime}) と test runtime (${testRuntime}) が一致しません。`,
    );
  }

  // sourceLayout validation
  validatePathTemplate(
    `profile "${name}".sourceLayout.sourceDir`,
    profile.sourceLayout.sourceDir,
  );
  validatePathTemplate(
    `profile "${name}".sourceLayout.testDir`,
    profile.sourceLayout.testDir,
  );
  validateScopePattern(
    `profile "${name}".sourceLayout.scopePattern`,
    profile.sourceLayout.scopePattern,
  );
  for (const prefix of profile.sourceLayout.additionalAllowedPrefixes) {
    validatePathTemplate(
      `profile "${name}".sourceLayout.additionalAllowedPrefixes`,
      prefix,
    );
  }
  if (profile.storybook) {
    validateResolvedStringArray(profile.storybook.renderCommand, `profile "${name}".storybook.renderCommand`);
    validateResolvedStringArray(profile.storybook.smokeCommand, `profile "${name}".storybook.smokeCommand`);
  }
  if (profile.claude) {
    validateResolvedProfileClaudeConfig(name, profile.claude, rootClaudeConfig);
  }
}

function validateStringArrayField(value: unknown, field: string): void {
  if (!Array.isArray(value) || value.length === 0) {
    throw new GuardError(`${field} は空でない文字列配列で指定してください。`);
  }
  for (const item of value) {
    if (typeof item !== "string" || item.length === 0) {
      throw new GuardError(`${field} の各要素は空でない文字列である必要があります。`);
    }
  }
}

function validateBundleRecord(
  value: Record<string, string[]> | undefined,
  field: string,
): void {
  if (value === undefined) return;
  if (typeof value !== "object" || Array.isArray(value)) {
    throw new GuardError(`${field} はオブジェクト形式で指定してください。`);
  }
  for (const [name, entries] of Object.entries(value)) {
    validateStringArrayField(entries, `${field}.${name}`);
  }
}

function validateProfileClaudeConfig(
  value: UserProfileClaudeConfig,
  field: string,
): void {
  if (typeof value !== "object" || Array.isArray(value)) {
    throw new GuardError(`${field} はオブジェクト形式で指定してください。`);
  }
  if (value.defaultAgent !== undefined && typeof value.defaultAgent !== "string") {
    throw new GuardError(`${field}.defaultAgent は文字列で指定してください。`);
  }
  if (value.defaultSkillBundles !== undefined) {
    validateStringArrayField(value.defaultSkillBundles, `${field}.defaultSkillBundles`);
  }
  if (value.defaultMcpBundles !== undefined) {
    validateStringArrayField(value.defaultMcpBundles, `${field}.defaultMcpBundles`);
  }
  if (value.stepOverrides === undefined) return;
  if (typeof value.stepOverrides !== "object" || Array.isArray(value.stepOverrides)) {
    throw new GuardError(`${field}.stepOverrides はオブジェクト形式で指定してください。`);
  }

  const validStepKeys = new Set(Object.values(FLOW_STEP));
  for (const [step, override] of Object.entries(value.stepOverrides)) {
    if (!validStepKeys.has(step as FlowStep)) {
      throw new GuardError(
        `${field}.stepOverrides に未知の step "${step}" が指定されています。利用可能: ${[...validStepKeys].join(", ")}`,
      );
    }
    if (!override || typeof override !== "object" || Array.isArray(override)) {
      throw new GuardError(`${field}.stepOverrides.${step} はオブジェクト形式で指定してください。`);
    }
    if (override.agent !== undefined && typeof override.agent !== "string") {
      throw new GuardError(`${field}.stepOverrides.${step}.agent は文字列で指定してください。`);
    }
    if (override.skillBundles !== undefined) {
      validateStringArrayField(override.skillBundles, `${field}.stepOverrides.${step}.skillBundles`);
    }
    if (override.mcpBundles !== undefined) {
      validateStringArrayField(override.mcpBundles, `${field}.stepOverrides.${step}.mcpBundles`);
    }
  }
}

function resolveClaudeConfig(user: UserClaudeConfig | undefined): ResolvedClaudeConfig {
  return {
    skillBundles: cloneBundleRecord(user?.skillBundles),
    mcpBundles: cloneBundleRecord(user?.mcpBundles),
  };
}

function cloneBundleRecord(
  bundles: Record<string, string[]> | undefined,
): Record<string, string[]> {
  if (!bundles) return {};
  return Object.fromEntries(
    Object.entries(bundles).map(([name, entries]) => [name, [...entries]]),
  );
}

function resolveProfileClaudeConfig(
  user: UserProfileClaudeConfig | undefined,
): ProfileClaudeConfig | undefined {
  if (!user) return undefined;

  const stepOverrides: Partial<Record<FlowStep, ClaudeStepOverrideConfig>> = {};
  for (const [step, override] of Object.entries(user.stepOverrides ?? {})) {
    stepOverrides[step as FlowStep] = {
      agent: override?.agent,
      skillBundles: [...(override?.skillBundles ?? [])],
      mcpBundles: [...(override?.mcpBundles ?? [])],
    };
  }

  return {
    defaultAgent: user.defaultAgent,
    defaultSkillBundles: [...(user.defaultSkillBundles ?? [])],
    defaultMcpBundles: [...(user.defaultMcpBundles ?? [])],
    stepOverrides,
  };
}

function validateResolvedProfileClaudeConfig(
  profileName: string,
  claude: ProfileClaudeConfig,
  rootClaudeConfig: ResolvedClaudeConfig,
): void {
  validateBundleRefs(
    claude.defaultSkillBundles,
    rootClaudeConfig.skillBundles,
    `profile "${profileName}".claude.defaultSkillBundles`,
  );
  validateBundleRefs(
    claude.defaultMcpBundles,
    rootClaudeConfig.mcpBundles,
    `profile "${profileName}".claude.defaultMcpBundles`,
  );

  for (const [step, override] of Object.entries(claude.stepOverrides)) {
    if (!override) continue;
    validateBundleRefs(
      override.skillBundles,
      rootClaudeConfig.skillBundles,
      `profile "${profileName}".claude.stepOverrides.${step}.skillBundles`,
    );
    validateBundleRefs(
      override.mcpBundles,
      rootClaudeConfig.mcpBundles,
      `profile "${profileName}".claude.stepOverrides.${step}.mcpBundles`,
    );
  }
}

function validateBundleRefs(
  bundleNames: string[],
  availableBundles: Record<string, string[]>,
  field: string,
): void {
  for (const bundleName of bundleNames) {
    if (!availableBundles[bundleName]) {
      throw new GuardError(
        `${field} に未知の bundle "${bundleName}" が指定されています。利用可能: ${Object.keys(availableBundles).join(", ") || "なし"}`,
      );
    }
  }
}

function validateResolvedStringArray(value: string[], field: string): void {
  if (value.length === 0) {
    throw new GuardError(`${field} は空配列にできません。`);
  }
  for (const item of value) {
    if (item.length === 0) {
      throw new GuardError(`${field} の各要素は空文字列にできません。`);
    }
  }
}

function validatePathTemplate(field: string, value: string): void {
  if (value.startsWith("/")) {
    throw new GuardError(`${field}: 絶対パスは指定できません: "${value}"`);
  }
  if (value.includes("..")) {
    throw new GuardError(
      `${field}: ".." を含むパスは指定できません: "${value}"`,
    );
  }
  // 許可プレースホルダ以外の {{ }} を拒否
  const withoutPlaceholders = value
    .replaceAll("{{category}}", "")
    .replaceAll("{{name}}", "");
  if (/\{\{/.test(withoutPlaceholders)) {
    throw new GuardError(
      `${field}: 未知のプレースホルダが含まれています: "${value}"。許可: {{category}}, {{name}}`,
    );
  }
  // CLI メタ文字禁止（* も禁止。scopePattern は別 validator）
  if (/[,)()*?\\]/.test(withoutPlaceholders)) {
    throw new GuardError(
      `${field}: 特殊文字（, ) ( * ? \\）は許可されていません: "${value}"`,
    );
  }
}

function validateScopePattern(field: string, value: string): void {
  // 末尾の /* または /** を除去してから validatePathTemplate
  const trimmed = value.replace(/\/\*{1,2}$/, "");
  validatePathTemplate(field, trimmed);
  // 末尾は /* か /** でなければならない
  if (!value.endsWith("/*") && !value.endsWith("/**")) {
    throw new GuardError(
      `${field}: scopePattern の末尾は "/*" または "/**" である必要があります: "${value}"`,
    );
  }
}

// === Profile 解決ユーティリティ ===

export function inferProfile(config: ResolvedConfig): string {
  const names = Object.keys(config.profiles);
  if (names.length === 1) return names[0];
  throw new GuardError(
    `複数の profile があります（${names.join(", ")}）。plan ファイルの frontmatter で profile を指定してください。`,
  );
}

export function resolveProfile(
  config: ResolvedConfig,
  profileName: string,
): ResolvedProfileConfig {
  const profile = config.profiles[profileName];
  if (!profile) {
    throw new GuardError(
      `profile "${profileName}" が見つかりません。${configLocationMessage()} の profiles を確認してください。利用可能: ${Object.keys(config.profiles).join(", ")}`,
    );
  }
  return profile;
}

function findConfigPath(projectRoot: string): string | null {
  for (const name of CONFIG_FILENAMES) {
    const configPath = join(projectRoot, name);
    if (existsSync(configPath)) {
      return configPath;
    }
  }
  return null;
}

function relativeConfigPath(projectRoot: string, filePath: string): string {
  const relativePath = relative(resolve(projectRoot), resolve(filePath));
  return relativePath || filePath;
}

function configLocationMessage(): string {
  return `${PREFERRED_CONFIG_PATH}（後方互換で ${LEGACY_CONFIG_PATH} も可）`;
}
