import { GuardError } from "../types.ts";

export type ArtifactValidationFacts = {
  concreteTestFileCount: number;
  targetTestFile: string;
  targetTestFilePresent: boolean;
  targetTestFileChanged: boolean;
  targetTestIntentCount: number | null;
  approvedCaseCount: number;
};

export function validateArtifactFacts(
  facts: ArtifactValidationFacts,
): {
  targetTestFileChanged: boolean;
  targetTestIntentCount: number | null;
  approvedCaseCount: number;
} {
  if (facts.concreteTestFileCount === 0) {
    throw new GuardError(
      `テスト生成後も収集対象のテストファイルが存在しません。少なくとも ${facts.targetTestFile} のようなテストファイルを生成してください。`,
    );
  }
  if (!facts.targetTestFilePresent) {
    throw new GuardError(
      `テスト生成後も主対象のテストファイル ${facts.targetTestFile} が存在しません。対象ファイルを直接更新してください。`,
    );
  }
  if (!facts.targetTestFileChanged) {
    throw new GuardError(
      `テスト生成後も主対象のテストファイル ${facts.targetTestFile} に変更がありません。まず対象ファイルを更新してください。`,
    );
  }
  if (
    facts.approvedCaseCount > 0 &&
    facts.targetTestIntentCount !== null &&
    facts.targetTestIntentCount > facts.approvedCaseCount + 2
  ) {
    throw new GuardError(
      `生成テストの test intent 数 (${facts.targetTestIntentCount}) が承認済みテストケース数 (${facts.approvedCaseCount}) から大きく逸脱しています。approved cases にない独自追加や不要分割をやめてください。`,
    );
  }

  return {
    targetTestFileChanged: facts.targetTestFileChanged,
    targetTestIntentCount: facts.targetTestIntentCount,
    approvedCaseCount: facts.approvedCaseCount,
  };
}
