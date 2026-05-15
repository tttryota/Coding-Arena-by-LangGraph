import { readFileSync, existsSync } from "node:fs";
import { join, relative, resolve } from "node:path";
import { parse as parseYaml } from "yaml";
import {
  CAPABILITY_POLICY_MODE,
  EXECUTION_CAPABILITY,
  type CapabilityPolicy,
  type CapabilityPolicyMode,
  type ExecutionCapability,
} from "./runner.ts";
import { GuardError, HarnessError } from "./types.ts";
import { LINT_REGISTRY, TEST_REGISTRY } from "./tool-adapter.ts";
import { FLOW_STEP } from "./steps.ts";
import type { FlowMode, FlowStep } from "./steps.ts";

export type ProviderType = "claude" | "codex" | "generic";

export type UserProviderConfig =
  | {
      type: "claude";
      timeoutMs?: number;
      model?: string;
      capabilities?: ExecutionCapability[];
      capabilityPolicy?: Partial<Record<ExecutionCapability, CapabilityPolicyMode>>;
    }
  | {
      type: "codex";
      sandbox?: string;
      timeoutMs?: number;
      heartbeatMs?: number;
      stallTimeoutMs?: number;
      capabilities?: ExecutionCapability[];
      capabilityPolicy?: Partial<Record<ExecutionCapability, CapabilityPolicyMode>>;
    }
  | {
      type: "generic";
      command: string;
      args: string[];
      promptFlag?: string;
      timeoutMs?: number;
      capabilities?: ExecutionCapability[];
      capabilityPolicy?: Partial<Record<ExecutionCapability, CapabilityPolicyMode>>;
    };

export type ResolvedProviderConfig =
  | {
      type: "claude";
      timeoutMs?: number;
      model?: string;
      capabilities: ExecutionCapability[];
      capabilityPolicy: CapabilityPolicy;
    }
  | {
      type: "codex";
      sandbox?: string;
      timeoutMs?: number;
      heartbeatMs?: number;
      stallTimeoutMs?: number;
      capabilities: ExecutionCapability[];
      capabilityPolicy: CapabilityPolicy;
    }
  | {
      type: "generic";
      command: string;
      args: string[];
      promptFlag?: string;
      timeoutMs?: number;
      capabilities: ExecutionCapability[];
      capabilityPolicy: CapabilityPolicy;
    };

export type UserSourceLayoutConfig = {
  sourceDir?: string;
  testDir?: string;
  scopePattern?: string;
  additionalAllowedPrefixes?: string[];
};

export type SourceLayoutConfig = {
  sourceDir: string;
  testDir: string;
  scopePattern: string;
  additionalAllowedPrefixes: string[];
};

export type UserStorybookConfig = {
  renderCommand?: string[];
  smokeCommand?: string[];
};

export type StorybookConfig = {
  renderCommand: string[];
  smokeCommand: string[];
};

export type UserStepContextOverrideConfig = {
  contextBundles?: string[];
  mcpBundles?: string[];
};

export type UserProfileContextConfig = {
  defaultContextBundles?: string[];
  defaultMcpBundles?: string[];
  stepOverrides?: Partial<Record<FlowStep, UserStepContextOverrideConfig>>;
};

export type UserProfileStepProviderConfig = {
  defaultProvider?: string;
  stepOverrides?: Partial<Record<FlowStep, string>>;
};

export type StepContextOverrideConfig = {
  contextBundles: string[];
  mcpBundles: string[];
};

export type ProfileContextConfig = {
  defaultContextBundles: string[];
  defaultMcpBundles: string[];
  stepOverrides: Partial<Record<FlowStep, StepContextOverrideConfig>>;
};

export type ProfileStepProviderConfig = {
  defaultProvider?: string;
  stepOverrides: Partial<Record<FlowStep, string>>;
};

export type UserContextConfig = {
  contextBundles?: Record<string, string[]>;
  mcpBundles?: Record<string, string[]>;
};

export type ResolvedContextConfig = {
  contextBundles: Record<string, string[]>;
  mcpBundles: Record<string, string[]>;
};

export type UserProfileConfig = {
  lint?: string[];
  test?: string;
  sourceLayout?: UserSourceLayoutConfig;
  storybook?: UserStorybookConfig;
  exec?: string | string[];
  toolRoot?: string;
  reviewCriteria?: string[];
  criteriaPreset?: "backend" | "frontend";
  context?: UserProfileContextConfig;
  stepProviders?: UserProfileStepProviderConfig;
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
  context?: ProfileContextConfig;
  stepProviders?: ProfileStepProviderConfig;
};

export type HarnessUserConfig = {
  profiles?: Record<string, UserProfileConfig>;
  providers?: Record<string, UserProviderConfig>;
  flow?: FlowMode;
  steps?: Partial<Record<FlowStep, string>>;
  templates?: Record<string, string | null>;
  context?: UserContextConfig;
};

export type ResolvedConfig = {
  profiles: Record<string, ResolvedProfileConfig>;
  providers: Record<string, ResolvedProviderConfig>;
  flow: FlowMode;
  steps: Partial<Record<FlowStep, string>>;
  templates: Record<string, string | null>;
  context: ResolvedContextConfig;
};

export type HarnessConfig = ResolvedConfig;

const PREFERRED_CONFIG_PATH = ".harness/harness.yml";
const LEGACY_CONFIG_PATH = ".harness.yml";
const CONFIG_FILENAMES = [
  PREFERRED_CONFIG_PATH,
  ".harness/harness.yaml",
  LEGACY_CONFIG_PATH,
  ".harness.yaml",
];

const DEFAULT_STEPS: Partial<Record<FlowStep, string>> = {
  test_generate: "codex",
  test_self_quality: "codex",
  test_external_review: "claude",
  impl_generate: "codex",
  impl_self_criteria: "codex",
  impl_self_quality: "codex",
  impl_external_review: "claude",
  lint_fix: "codex",
  apply_fixes: "codex",
  judgment_summary: "codex",
  judge_minor: "codex",
  spec_generate: "codex",
  test_case_generate: "codex",
  component_generate: "codex",
  component_self_review: "codex",
  page_generate: "codex",
  page_review_design: "codex",
  page_review_behavior: "codex",
  page_review_code: "codex",
  page_browser_verify: "codex",
};

const ALL_CAPABILITIES = Object.values(EXECUTION_CAPABILITY);
const ALL_POLICY_MODES = new Set(Object.values(CAPABILITY_POLICY_MODE));

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

  validateUserConfigShape(userConfig);
  const migrated = requireProfiles(userConfig);

  const providers = resolveProviders(migrated.providers ?? { claude: { type: "claude" } });
  const providerNames = Object.keys(providers);
  const stepDefault = providers.codex ? "codex" : providerNames[0] ?? "claude";
  const defaultSteps: Partial<Record<FlowStep, string>> = {};
  for (const [key, value] of Object.entries(DEFAULT_STEPS)) {
    defaultSteps[key as FlowStep] = value && providers[value] ? value : stepDefault;
  }

  const resolved: ResolvedConfig = {
    profiles: resolveProfiles(migrated.profiles ?? {}, projectRoot),
    providers,
    flow: migrated.flow ?? "full",
    steps: { ...defaultSteps, ...migrated.steps },
    templates: migrated.templates ?? {},
    context: resolveContextConfig(migrated.context),
  };

  validateConfig(resolved);
  return resolved;
}

function validateUserConfigShape(config: HarnessUserConfig): void {
  if (config.profiles !== undefined) {
    if (typeof config.profiles !== "object" || Array.isArray(config.profiles)) {
      throw new GuardError("profiles はオブジェクト形式で指定してください。");
    }
    for (const [name, profile] of Object.entries(config.profiles)) {
      validateUserProfileConfig(name, profile);
    }
  }

  if (config.providers !== undefined) {
    if (typeof config.providers !== "object" || Array.isArray(config.providers)) {
      throw new GuardError("providers はオブジェクト形式で指定してください。");
    }
    for (const [name, provider] of Object.entries(config.providers)) {
      validateUserProviderConfig(name, provider);
    }
  }

  if (config.context !== undefined) {
    validateBundleRecord(config.context.contextBundles, "context.contextBundles");
    validateBundleRecord(config.context.mcpBundles, "context.mcpBundles");
  }

  if (config.steps !== undefined) {
    if (typeof config.steps !== "object" || Array.isArray(config.steps)) {
      throw new GuardError("steps はオブジェクト形式で指定してください。");
    }
  }

  if (config.templates !== undefined && (typeof config.templates !== "object" || Array.isArray(config.templates))) {
    throw new GuardError("templates はオブジェクト形式で指定してください。");
  }

  if (config.flow !== undefined && config.flow !== "full" && config.flow !== "light") {
    throw new GuardError(`flow は "full" または "light" で指定してください。受け取った値: "${config.flow}"`);
  }
}

function validateUserProfileConfig(name: string, profile: UserProfileConfig | undefined): void {
  if (!profile || typeof profile !== "object" || Array.isArray(profile)) {
    throw new GuardError(`profile "${name}" はオブジェクト形式で指定してください。`);
  }
  if (profile.lint !== undefined) validateStringArrayField(profile.lint, `profile "${name}".lint`);
  if (profile.test !== undefined && typeof profile.test !== "string") {
    throw new GuardError(`profile "${name}".test は文字列で指定してください。`);
  }
  if (profile.reviewCriteria !== undefined) {
    validateStringArrayField(profile.reviewCriteria, `profile "${name}".reviewCriteria`);
  }
  if (profile.sourceLayout !== undefined) {
    if (typeof profile.sourceLayout !== "object" || Array.isArray(profile.sourceLayout)) {
      throw new GuardError(`profile "${name}".sourceLayout はオブジェクト形式で指定してください。`);
    }
    const layout = profile.sourceLayout;
    if (layout.sourceDir !== undefined && typeof layout.sourceDir !== "string") {
      throw new GuardError(`profile "${name}".sourceLayout.sourceDir は文字列で指定してください。`);
    }
    if (layout.testDir !== undefined && typeof layout.testDir !== "string") {
      throw new GuardError(`profile "${name}".sourceLayout.testDir は文字列で指定してください。`);
    }
    if (layout.scopePattern !== undefined && typeof layout.scopePattern !== "string") {
      throw new GuardError(`profile "${name}".sourceLayout.scopePattern は文字列で指定してください。`);
    }
    if (layout.additionalAllowedPrefixes !== undefined) {
      validateStringArrayField(
        layout.additionalAllowedPrefixes,
        `profile "${name}".sourceLayout.additionalAllowedPrefixes`,
      );
    }
  }
  if (profile.storybook !== undefined) {
    if (typeof profile.storybook !== "object" || Array.isArray(profile.storybook)) {
      throw new GuardError(`profile "${name}".storybook はオブジェクト形式で指定してください。`);
    }
    if (profile.storybook.renderCommand !== undefined) {
      validateStringArrayField(profile.storybook.renderCommand, `profile "${name}".storybook.renderCommand`);
    }
    if (profile.storybook.smokeCommand !== undefined) {
      validateStringArrayField(profile.storybook.smokeCommand, `profile "${name}".storybook.smokeCommand`);
    }
  }
  if (profile.criteriaPreset !== undefined && profile.criteriaPreset !== "backend" && profile.criteriaPreset !== "frontend") {
    throw new GuardError(`profile "${name}".criteriaPreset は "backend" または "frontend" で指定してください。`);
  }
  if (profile.toolRoot !== undefined && typeof profile.toolRoot !== "string") {
    throw new GuardError(`profile "${name}".toolRoot は文字列で指定してください。`);
  }
  if (profile.context !== undefined) {
    validateProfileContextConfig(profile.context, `profile "${name}".context`);
  }
  if (profile.stepProviders !== undefined) {
    validateProfileStepProviderConfig(profile.stepProviders, `profile "${name}".stepProviders`);
  }
}

function validateUserProviderConfig(name: string, provider: UserProviderConfig | undefined): void {
  if (!provider || typeof provider !== "object" || !("type" in provider)) {
    throw new GuardError(`provider "${name}" には type フィールドが必要です。`);
  }
  const validTypes: ProviderType[] = ["claude", "codex", "generic"];
  if (!validTypes.includes(provider.type)) {
    throw new GuardError(
      `provider "${name}" の type "${String(provider.type)}" は不正です。利用可能: ${validTypes.join(", ")}`,
    );
  }
  if (provider.type === "generic") {
    if (typeof provider.command !== "string" || provider.command.length === 0) {
      throw new GuardError(`provider "${name}" (type: generic) には command が必要です。`);
    }
    validateStringArrayField(provider.args, `provider "${name}".args`);
    if (provider.promptFlag !== undefined && typeof provider.promptFlag !== "string") {
      throw new GuardError(`provider "${name}".promptFlag は文字列で指定してください。`);
    }
  }
  if (provider.timeoutMs !== undefined && (typeof provider.timeoutMs !== "number" || provider.timeoutMs <= 0)) {
    throw new GuardError(`provider "${name}".timeoutMs は正の数値である必要があります。`);
  }
  if (provider.type === "codex" && provider.heartbeatMs !== undefined && (typeof provider.heartbeatMs !== "number" || provider.heartbeatMs <= 0)) {
    throw new GuardError(`provider "${name}".heartbeatMs は正の数値で指定してください。`);
  }
  if (provider.type === "codex" && provider.stallTimeoutMs !== undefined && (typeof provider.stallTimeoutMs !== "number" || provider.stallTimeoutMs <= 0)) {
    throw new GuardError(`provider "${name}".stallTimeoutMs は正の数値で指定してください。`);
  }
  if (provider.type === "claude" && provider.model !== undefined && typeof provider.model !== "string") {
    throw new GuardError(`provider "${name}".model は文字列で指定してください。`);
  }
  if (provider.type === "codex" && provider.sandbox !== undefined && typeof provider.sandbox !== "string") {
    throw new GuardError(`provider "${name}".sandbox は文字列で指定してください。`);
  }
  validateCapabilityList(provider.capabilities, `provider "${name}".capabilities`);
  validateCapabilityPolicyShape(provider.capabilityPolicy, `provider "${name}".capabilityPolicy`);
}

function requireProfiles(config: HarnessUserConfig): HarnessUserConfig {
  if (config.profiles && Object.keys(config.profiles).length > 0) return config;
  throw new GuardError(
    `profiles が定義されていません。${configLocationMessage()} に profiles を追加してください。\n\`tdd-harness init\` でセットアップガイドを表示できます。`,
  );
}

function resolveProfiles(
  profiles: Record<string, UserProfileConfig>,
  projectRoot: string,
): Record<string, ResolvedProfileConfig> {
  return Object.fromEntries(
    Object.entries(profiles).map(([name, user]) => [name, resolveOneProfile(user, projectRoot)]),
  );
}

function resolveOneProfile(user: UserProfileConfig, projectRoot: string): ResolvedProfileConfig {
  if (user.lint !== undefined) {
    for (const tool of user.lint) {
      if (!LINT_REGISTRY[tool]) {
        throw new GuardError(`未知の lint ツール "${tool}"。利用可能: ${Object.keys(LINT_REGISTRY).join(", ")}`);
      }
    }
  }
  if (user.test !== undefined && !TEST_REGISTRY[user.test]) {
    throw new GuardError(`未知のテストランナー "${user.test}"。利用可能: ${Object.keys(TEST_REGISTRY).join(", ")}`);
  }

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
    if (testRuntime !== "python") {
      throw new GuardError(`lint が未指定ですが、test "${test}" に対するデフォルト lint がありません。lint を明示指定してください。`);
    }
    lint = ["ruff", "mypy"];
  } else {
    lint = user.lint!;
    const lintRuntime = LINT_REGISTRY[lint[0]]?.runtime;
    if (lintRuntime !== "python") {
      throw new GuardError(`test が未指定ですが、lint runtime (${lintRuntime}) に対するデフォルト test がありません。test を明示指定してください。`);
    }
    test = "pytest";
  }

  const userLayout = user.sourceLayout;
  const sourceLayout: SourceLayoutConfig = {
    sourceDir: userLayout?.sourceDir ?? "backend/{{category}}",
    testDir: userLayout?.testDir ?? "backend/{{category}}/tests",
    scopePattern: userLayout?.scopePattern ?? `${userLayout?.sourceDir ?? "backend/{{category}}"}/*`,
    additionalAllowedPrefixes: userLayout?.additionalAllowedPrefixes ?? ["docs/reviews/"],
  };

  return {
    lint,
    test,
    sourceLayout,
    storybook: user.storybook
      ? {
          renderCommand: [...(user.storybook.renderCommand ?? [])],
          smokeCommand: [...(user.storybook.smokeCommand ?? [])],
        }
      : undefined,
    exec: normalizeExec(user.exec),
    toolRoot: resolve(projectRoot, user.toolRoot ?? "."),
    reviewCriteria: user.reviewCriteria ?? [],
    criteriaPreset: user.criteriaPreset,
    context: resolveProfileContextConfig(user.context),
    stepProviders: resolveProfileStepProviderConfig(user.stepProviders),
  };
}

function resolveProviders(
  providers: Record<string, UserProviderConfig>,
): Record<string, ResolvedProviderConfig> {
  return Object.fromEntries(
    Object.entries(providers).map(([name, provider]) => [name, resolveProvider(provider)]),
  );
}

function resolveProvider(provider: UserProviderConfig): ResolvedProviderConfig {
  const capabilities = uniqueStrings(provider.capabilities ?? []);
  const capabilityPolicy = resolveCapabilityPolicy(provider.capabilityPolicy);

  if (provider.type === "claude") {
    return {
      type: "claude",
      timeoutMs: provider.timeoutMs,
      model: provider.model,
      capabilities,
      capabilityPolicy,
    };
  }
  if (provider.type === "codex") {
    return {
      type: "codex",
      sandbox: provider.sandbox,
      timeoutMs: provider.timeoutMs,
      heartbeatMs: provider.heartbeatMs,
      stallTimeoutMs: provider.stallTimeoutMs,
      capabilities,
      capabilityPolicy,
    };
  }
  return {
    type: "generic",
    command: provider.command,
    args: [...provider.args],
    promptFlag: provider.promptFlag,
    timeoutMs: provider.timeoutMs,
    capabilities,
    capabilityPolicy,
  };
}

function resolveCapabilityPolicy(
  value: Partial<Record<ExecutionCapability, CapabilityPolicyMode>> | undefined,
): CapabilityPolicy {
  const policy: Partial<Record<ExecutionCapability, CapabilityPolicyMode>> = {};
  for (const capability of ALL_CAPABILITIES) {
    policy[capability] = value?.[capability] ?? CAPABILITY_POLICY_MODE.REJECT;
  }
  return policy as CapabilityPolicy;
}

function normalizeExec(raw: unknown): string[] {
  if (raw === undefined || raw === null) return [];
  if (Array.isArray(raw)) {
    for (const elem of raw) {
      if (typeof elem !== "string") {
        throw new HarnessError(`exec の要素は文字列である必要があります。不正な要素: ${JSON.stringify(elem)}`);
      }
      validateExecElement(elem);
    }
    return raw;
  }
  if (typeof raw === "string") {
    validateExecElement(raw);
    return [raw];
  }
  throw new HarnessError("exec は配列で指定してください。例: exec: [poetry, run]");
}

function validateExecElement(elem: string): void {
  if (elem.length === 0) throw new HarnessError("exec の要素に空文字列は指定できません。");
  if (elem !== elem.trim()) {
    throw new HarnessError(`exec の要素に前後の空白を含む文字列は指定できません: "${elem}"`);
  }
}

function validateConfig(config: ResolvedConfig): void {
  if (Object.keys(config.profiles).length === 0) {
    throw new GuardError(`profiles が定義されていません。${configLocationMessage()} に profiles を追加してください。`);
  }
  if (Object.keys(config.providers).length === 0) {
    throw new GuardError("providers が定義されていません。");
  }

  const validStepKeys = new Set(Object.values(FLOW_STEP));
  const providerNames = Object.keys(config.providers);

  for (const [name, profile] of Object.entries(config.profiles)) {
    validateProfile(name, profile, config.context);
    validateProfileProviderRefs(name, profile, config.providers);
  }
  for (const [step, providerName] of Object.entries(config.steps)) {
    if (!validStepKeys.has(step as FlowStep)) {
      throw new GuardError(`steps に未知のキー "${step}" が指定されています。利用可能: ${[...validStepKeys].join(", ")}`);
    }
    if (providerName && !config.providers[providerName]) {
      throw new GuardError(`steps.${step} に指定された provider "${providerName}" が providers に存在しません。利用可能: ${providerNames.join(", ")}`);
    }
  }
}

function validateProfileProviderRefs(
  profileName: string,
  profile: ResolvedProfileConfig,
  providers: Record<string, ResolvedProviderConfig>,
): void {
  const available = Object.keys(providers);
  const stepProviders = profile.stepProviders;
  if (!stepProviders) return;
  if (stepProviders.defaultProvider && !providers[stepProviders.defaultProvider]) {
    throw new GuardError(
      `profile "${profileName}".stepProviders.defaultProvider に指定された provider "${stepProviders.defaultProvider}" が存在しません。利用可能: ${available.join(", ")}`,
    );
  }
  for (const [step, providerName] of Object.entries(stepProviders.stepOverrides)) {
    if (!providers[providerName]) {
      throw new GuardError(
        `profile "${profileName}".stepProviders.stepOverrides.${step} に指定された provider "${providerName}" が存在しません。利用可能: ${available.join(", ")}`,
      );
    }
  }
}

function validateProfile(
  name: string,
  profile: ResolvedProfileConfig,
  rootContextConfig: ResolvedContextConfig,
): void {
  if (profile.lint.length === 0) {
    throw new GuardError(`profile "${name}": lint ツールが指定されていません。`);
  }
  for (const tool of profile.lint) {
    if (!LINT_REGISTRY[tool]) {
      throw new GuardError(`profile "${name}": 未知の lint ツール "${tool}"。利用可能: ${Object.keys(LINT_REGISTRY).join(", ")}`);
    }
  }
  const runtimes = new Set(profile.lint.map((tool) => LINT_REGISTRY[tool].runtime));
  if (runtimes.size > 1) {
    throw new GuardError(`profile "${name}": 異なる runtime の lint ツールを混在させることはできません。`);
  }
  if (!TEST_REGISTRY[profile.test]) {
    throw new GuardError(`profile "${name}": 未知のテストランナー "${profile.test}"。利用可能: ${Object.keys(TEST_REGISTRY).join(", ")}`);
  }
  const lintRuntime = [...runtimes][0];
  const testRuntime = TEST_REGISTRY[profile.test].runtime;
  if (lintRuntime && lintRuntime !== testRuntime) {
    throw new GuardError(`profile "${name}": lint runtime (${lintRuntime}) と test runtime (${testRuntime}) が一致しません。`);
  }
  validatePathTemplate(`profile "${name}".sourceLayout.sourceDir`, profile.sourceLayout.sourceDir);
  validatePathTemplate(`profile "${name}".sourceLayout.testDir`, profile.sourceLayout.testDir);
  validateScopePattern(`profile "${name}".sourceLayout.scopePattern`, profile.sourceLayout.scopePattern);
  for (const prefix of profile.sourceLayout.additionalAllowedPrefixes) {
    validatePathTemplate(`profile "${name}".sourceLayout.additionalAllowedPrefixes`, prefix);
  }
  if (profile.storybook) {
    validateResolvedStringArray(profile.storybook.renderCommand, `profile "${name}".storybook.renderCommand`);
    validateResolvedStringArray(profile.storybook.smokeCommand, `profile "${name}".storybook.smokeCommand`);
  }
  if (profile.context) {
    validateResolvedProfileContextConfig(name, profile.context, rootContextConfig);
  }
  if (profile.stepProviders) {
    validateResolvedProfileStepProviders(name, profile.stepProviders);
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

function validateBundleRecord(value: Record<string, string[]> | undefined, field: string): void {
  if (value === undefined) return;
  if (typeof value !== "object" || Array.isArray(value)) {
    throw new GuardError(`${field} はオブジェクト形式で指定してください。`);
  }
  for (const [name, entries] of Object.entries(value)) {
    validateStringArrayField(entries, `${field}.${name}`);
  }
}

function validateCapabilityList(value: ExecutionCapability[] | undefined, field: string): void {
  if (value === undefined) return;
  if (!Array.isArray(value)) {
    throw new GuardError(`${field} は配列で指定してください。`);
  }
  for (const capability of value) {
    if (!ALL_CAPABILITIES.includes(capability)) {
      throw new GuardError(`${field} に未知の capability "${capability}" が指定されています。`);
    }
  }
}

function validateCapabilityPolicyShape(
  value: Partial<Record<ExecutionCapability, CapabilityPolicyMode>> | undefined,
  field: string,
): void {
  if (value === undefined) return;
  if (typeof value !== "object" || Array.isArray(value)) {
    throw new GuardError(`${field} はオブジェクト形式で指定してください。`);
  }
  for (const [capability, mode] of Object.entries(value)) {
    if (!ALL_CAPABILITIES.includes(capability as ExecutionCapability)) {
      throw new GuardError(`${field} に未知の capability "${capability}" が指定されています。`);
    }
    if (!ALL_POLICY_MODES.has(mode as CapabilityPolicyMode)) {
      throw new GuardError(`${field}.${capability} は native / degrade_to_prompt / reject のいずれかで指定してください。`);
    }
  }
}

function validateProfileContextConfig(value: UserProfileContextConfig, field: string): void {
  if (typeof value !== "object" || Array.isArray(value)) {
    throw new GuardError(`${field} はオブジェクト形式で指定してください。`);
  }
  if (value.defaultContextBundles !== undefined) {
    validateStringArrayField(value.defaultContextBundles, `${field}.defaultContextBundles`);
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
      throw new GuardError(`${field}.stepOverrides に未知の step "${step}" が指定されています。`);
    }
    if (!override || typeof override !== "object" || Array.isArray(override)) {
      throw new GuardError(`${field}.stepOverrides.${step} はオブジェクト形式で指定してください。`);
    }
    if (override.contextBundles !== undefined) {
      validateStringArrayField(override.contextBundles, `${field}.stepOverrides.${step}.contextBundles`);
    }
    if (override.mcpBundles !== undefined) {
      validateStringArrayField(override.mcpBundles, `${field}.stepOverrides.${step}.mcpBundles`);
    }
  }
}

function validateProfileStepProviderConfig(value: UserProfileStepProviderConfig, field: string): void {
  if (typeof value !== "object" || Array.isArray(value)) {
    throw new GuardError(`${field} はオブジェクト形式で指定してください。`);
  }
  if (value.defaultProvider !== undefined && typeof value.defaultProvider !== "string") {
    throw new GuardError(`${field}.defaultProvider は文字列で指定してください。`);
  }
  if (value.stepOverrides === undefined) return;
  if (typeof value.stepOverrides !== "object" || Array.isArray(value.stepOverrides)) {
    throw new GuardError(`${field}.stepOverrides はオブジェクト形式で指定してください。`);
  }
  const validStepKeys = new Set(Object.values(FLOW_STEP));
  for (const [step, providerName] of Object.entries(value.stepOverrides)) {
    if (!validStepKeys.has(step as FlowStep)) {
      throw new GuardError(`${field}.stepOverrides に未知の step "${step}" が指定されています。`);
    }
    if (typeof providerName !== "string" || providerName.length === 0) {
      throw new GuardError(`${field}.stepOverrides.${step} は空でない provider 名で指定してください。`);
    }
  }
}

function resolveContextConfig(user: UserContextConfig | undefined): ResolvedContextConfig {
  return {
    contextBundles: cloneBundleRecord(user?.contextBundles),
    mcpBundles: cloneBundleRecord(user?.mcpBundles),
  };
}

function cloneBundleRecord(bundles: Record<string, string[]> | undefined): Record<string, string[]> {
  if (!bundles) return {};
  return Object.fromEntries(
    Object.entries(bundles).map(([name, entries]) => [name, [...entries]]),
  );
}

function resolveProfileContextConfig(user: UserProfileContextConfig | undefined): ProfileContextConfig | undefined {
  if (!user) return undefined;
  const stepOverrides: Partial<Record<FlowStep, StepContextOverrideConfig>> = {};
  for (const [step, override] of Object.entries(user.stepOverrides ?? {})) {
    stepOverrides[step as FlowStep] = {
      contextBundles: [...(override?.contextBundles ?? [])],
      mcpBundles: [...(override?.mcpBundles ?? [])],
    };
  }
  return {
    defaultContextBundles: [...(user.defaultContextBundles ?? [])],
    defaultMcpBundles: [...(user.defaultMcpBundles ?? [])],
    stepOverrides,
  };
}

function resolveProfileStepProviderConfig(
  user: UserProfileStepProviderConfig | undefined,
): ProfileStepProviderConfig | undefined {
  if (!user) return undefined;
  return {
    defaultProvider: user.defaultProvider,
    stepOverrides: Object.fromEntries(
      Object.entries(user.stepOverrides ?? {}).map(([step, providerName]) => [step, providerName]),
    ) as Partial<Record<FlowStep, string>>,
  };
}

function validateResolvedProfileContextConfig(
  profileName: string,
  context: ProfileContextConfig,
  rootContextConfig: ResolvedContextConfig,
): void {
  validateBundleRefs(context.defaultContextBundles, rootContextConfig.contextBundles, `profile "${profileName}".context.defaultContextBundles`);
  validateBundleRefs(context.defaultMcpBundles, rootContextConfig.mcpBundles, `profile "${profileName}".context.defaultMcpBundles`);
  for (const [step, override] of Object.entries(context.stepOverrides)) {
    if (!override) continue;
    validateBundleRefs(override.contextBundles, rootContextConfig.contextBundles, `profile "${profileName}".context.stepOverrides.${step}.contextBundles`);
    validateBundleRefs(override.mcpBundles, rootContextConfig.mcpBundles, `profile "${profileName}".context.stepOverrides.${step}.mcpBundles`);
  }
}

function validateResolvedProfileStepProviders(
  profileName: string,
  stepProviders: ProfileStepProviderConfig,
): void {
  if (stepProviders.defaultProvider !== undefined && stepProviders.defaultProvider.trim() === "") {
    throw new GuardError(`profile "${profileName}".stepProviders.defaultProvider は空文字列にできません。`);
  }
  for (const [step, providerName] of Object.entries(stepProviders.stepOverrides)) {
    if (!providerName || providerName.trim() === "") {
      throw new GuardError(`profile "${profileName}".stepProviders.stepOverrides.${step} は空文字列にできません。`);
    }
  }
}

function validateBundleRefs(
  bundleNames: string[],
  availableBundles: Record<string, string[]>,
  field: string,
): void {
  for (const bundleName of bundleNames) {
    if (!availableBundles[bundleName]) {
      throw new GuardError(`${field} に未知の bundle "${bundleName}" が指定されています。利用可能: ${Object.keys(availableBundles).join(", ") || "なし"}`);
    }
  }
}

function uniqueStrings<T extends string>(values: T[]): T[] {
  const seen = new Set<T>();
  const result: T[] = [];
  for (const value of values) {
    if (seen.has(value)) continue;
    seen.add(value);
    result.push(value);
  }
  return result;
}

function validateResolvedStringArray(value: string[], field: string): void {
  if (value.length === 0) throw new GuardError(`${field} は空配列にできません。`);
  for (const item of value) {
    if (item.length === 0) throw new GuardError(`${field} の各要素は空文字列にできません。`);
  }
}

function validatePathTemplate(field: string, value: string): void {
  if (value.startsWith("/")) {
    throw new GuardError(`${field}: 絶対パスは指定できません: "${value}"`);
  }
  if (value.includes("..")) {
    throw new GuardError(`${field}: ".." を含むパスは指定できません: "${value}"`);
  }
  const withoutPlaceholders = value
    .replaceAll("{{category}}", "")
    .replaceAll("{{name}}", "");
  if (/\{\{/.test(withoutPlaceholders)) {
    throw new GuardError(`${field}: 未知のプレースホルダが含まれています: "${value}"。許可: {{category}}, {{name}}`);
  }
  if (/[,)()*?\\]/.test(withoutPlaceholders)) {
    throw new GuardError(`${field}: 特殊文字（, ) ( * ? \\）は許可されていません: "${value}"`);
  }
}

function validateScopePattern(field: string, value: string): void {
  const trimmed = value.replace(/\/\*{1,2}$/, "");
  validatePathTemplate(field, trimmed);
  if (!value.endsWith("/*") && !value.endsWith("/**")) {
    throw new GuardError(`${field}: scopePattern の末尾は "/*" または "/**" である必要があります: "${value}"`);
  }
}

export function inferProfile(config: ResolvedConfig): string {
  const names = Object.keys(config.profiles);
  if (names.length === 1) return names[0];
  throw new GuardError(`複数の profile があります（${names.join(", ")}）。plan ファイルの frontmatter で profile を指定してください。`);
}

export function resolveProfile(config: ResolvedConfig, profileName: string): ResolvedProfileConfig {
  const profile = config.profiles[profileName];
  if (!profile) {
    throw new GuardError(`profile "${profileName}" が見つかりません。${configLocationMessage()} の profiles を確認してください。利用可能: ${Object.keys(config.profiles).join(", ")}`);
  }
  return profile;
}

function findConfigPath(projectRoot: string): string | null {
  for (const name of CONFIG_FILENAMES) {
    const configPath = join(projectRoot, name);
    if (existsSync(configPath)) return configPath;
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
