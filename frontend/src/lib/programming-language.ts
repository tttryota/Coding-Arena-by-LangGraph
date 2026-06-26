export const PROGRAMMING_LANGUAGE_STORAGE_KEY =
  "competitive-programming-language";

export function codePlaceholder(language: string) {
  const placeholders: Record<string, string> = {
    python: "# Python で解答を書いてください",
    typescript: "// TypeScript で解答を書いてください",
  };
  return placeholders[language] ?? `// ${language} で解答を書いてください`;
}
