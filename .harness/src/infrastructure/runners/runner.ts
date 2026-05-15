import type { HarnessLogger } from "../logging/logger.ts";
import { GuardError } from "../../shared/types.ts";

export const EXECUTION_CAPABILITY = {
  SESSION_RESUME: "session_resume",
  SYSTEM_PROMPT: "system_prompt",
  ALLOWED_TOOLS: "allowed_tools",
  AGENT: "agent",
  MCP_CONFIG: "mcp_config",
} as const;

export type ExecutionCapability =
  (typeof EXECUTION_CAPABILITY)[keyof typeof EXECUTION_CAPABILITY];

export const CAPABILITY_POLICY_MODE = {
  NATIVE: "native",
  DEGRADE_TO_PROMPT: "degrade_to_prompt",
  REJECT: "reject",
} as const;

export type CapabilityPolicyMode =
  (typeof CAPABILITY_POLICY_MODE)[keyof typeof CAPABILITY_POLICY_MODE];

export type ExecutionRequest = {
  prompt: string;
  cwd?: string;
  timeoutMs?: number;
  allowedTools?: string[];
  appendSystemPrompt?: string;
  sessionId?: string;
  agent?: string;
  mcpConfigs?: string[];
  observability?: {
    step?: string;
    benchmarkMode?: string;
    primaryTargetFile?: string;
    relatedFiles?: string[];
  };
};

export type ExecutionResult = {
  text: string;
  sessionId?: string;
  metadata?: {
    costUsd?: number | null;
    inputTokens?: number;
    outputTokens?: number;
    cacheCreationInputTokens?: number;
    cacheReadInputTokens?: number;
  };
};

export type ExecutionService = {
  readonly name: string;
  readonly capabilities: ReadonlySet<ExecutionCapability>;
  execute(request: ExecutionRequest, logger?: HarnessLogger): Promise<ExecutionResult>;
};

export type CapabilityPolicy = Record<ExecutionCapability, CapabilityPolicyMode>;

export type ExecutionProviderDefinition = {
  name: string;
  service: ExecutionService;
  policy: CapabilityPolicy;
};

export type ExecutableRunner = {
  readonly name: string;
  readonly capabilities: ReadonlySet<ExecutionCapability>;
  run(request: ExecutionRequest, logger?: HarnessLogger): Promise<ExecutionResult>;
  execute(request: ExecutionRequest, logger?: HarnessLogger): Promise<ExecutionResult>;
};

export function createRunner(
  service: ExecutionService,
  policy: CapabilityPolicy,
): ExecutableRunner {
  async function execute(
    request: ExecutionRequest,
    logger?: HarnessLogger,
  ): Promise<ExecutionResult> {
    return service.execute(applyCapabilityPolicy(service, policy, request), logger);
  }

  return {
    name: service.name,
    capabilities: service.capabilities,
    run: execute,
    execute,
  };
}

export function applyCapabilityPolicy(
  service: ExecutionService,
  policy: CapabilityPolicy,
  request: ExecutionRequest,
): ExecutionRequest {
  const normalized = { ...request };

  if (normalized.appendSystemPrompt) {
    const mode = policy[EXECUTION_CAPABILITY.SYSTEM_PROMPT];
    normalized.appendSystemPrompt = normalizeCapability(
      service,
      normalized.appendSystemPrompt,
      EXECUTION_CAPABILITY.SYSTEM_PROMPT,
      mode,
      (value) => {
        normalized.prompt = joinPromptSections([
          normalized.prompt,
          "---",
          "## Additional Context",
          value,
        ]);
        return undefined;
      },
    );
  }

  if (normalized.allowedTools && normalized.allowedTools.length > 0) {
    const mode = policy[EXECUTION_CAPABILITY.ALLOWED_TOOLS];
    normalized.allowedTools = normalizeCapability(
      service,
      normalized.allowedTools,
      EXECUTION_CAPABILITY.ALLOWED_TOOLS,
      mode,
      (value) => {
        const writePatterns = value.filter((tool) => tool.startsWith("Write(") || tool.startsWith("Edit("));
        if (writePatterns.length > 0) {
          normalized.prompt = joinPromptSections([
            normalized.prompt,
            "## File Scope Constraint",
            `Only modify files matching: ${writePatterns.join(", ")}`,
            "Touch one of the allowed target files early in the turn. Avoid broad repository exploration before you have opened or edited the primary target file unless a directly related config file is required.",
          ]);
        }
        return undefined;
      },
    );
  }

  if (normalized.agent) {
    const mode = policy[EXECUTION_CAPABILITY.AGENT];
    normalized.agent = normalizeCapability(
      service,
      normalized.agent,
      EXECUTION_CAPABILITY.AGENT,
      mode,
      (value) => {
        normalized.prompt = joinPromptSections([
          normalized.prompt,
          "## Requested Agent Role",
          value,
        ]);
        return undefined;
      },
    );
  }

  if (normalized.mcpConfigs && normalized.mcpConfigs.length > 0) {
    const mode = policy[EXECUTION_CAPABILITY.MCP_CONFIG];
    normalized.mcpConfigs = normalizeCapability(
      service,
      normalized.mcpConfigs,
      EXECUTION_CAPABILITY.MCP_CONFIG,
      mode,
      (value) => {
        normalized.prompt = joinPromptSections([
          normalized.prompt,
          "## MCP Context Constraint",
          `Use only the following MCP configurations if the provider supports them: ${value.join(", ")}`,
        ]);
        return undefined;
      },
    );
  }

  if (normalized.sessionId) {
    const mode = policy[EXECUTION_CAPABILITY.SESSION_RESUME];
    normalized.sessionId = normalizeCapability(
      service,
      normalized.sessionId,
      EXECUTION_CAPABILITY.SESSION_RESUME,
      mode,
      () => {
        throw new GuardError("session_resume は degrade_to_prompt にできません。native または reject を指定してください。");
      },
    );
  }

  return normalized;
}

function normalizeCapability<T>(
  service: ExecutionService,
  value: T,
  capability: ExecutionCapability,
  mode: CapabilityPolicyMode,
  degrade: (value: T) => T | undefined,
): T | undefined {
  switch (mode) {
    case CAPABILITY_POLICY_MODE.NATIVE:
      ensureServiceCapability(service, capability);
      return value;
    case CAPABILITY_POLICY_MODE.DEGRADE_TO_PROMPT:
      return degrade(value);
    case CAPABILITY_POLICY_MODE.REJECT:
      throw new GuardError(
        `provider "${service.name}" は capability "${capability}" をサポートしません。`,
      );
  }
}

function ensureServiceCapability(
  service: ExecutionService,
  capability: ExecutionCapability,
): void {
  if (!service.capabilities.has(capability)) {
    throw new GuardError(
      `provider "${service.name}" に capability "${capability}" が宣言されていません。`,
    );
  }
}

function joinPromptSections(sections: Array<string | undefined>): string {
  return sections
    .map((section) => section?.trim())
    .filter((section): section is string => Boolean(section))
    .join("\n\n");
}
