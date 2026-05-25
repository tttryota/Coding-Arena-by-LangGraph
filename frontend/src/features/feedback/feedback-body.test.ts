import { describe, it, expect } from "vitest";
import { parseFeedbackBody } from "./feedback-body";

describe("parseFeedbackBody", () => {
  describe("frontend spec format (bracket, inline)", () => {
    it("parses all three sections", () => {
      const body = [
        "[反映先ロードマップ: TypeScript / 型システム / ジェネリクス]",
        "正確性チェック: ジェネリクスの説明は概ね正確です。",
        "改善提案:",
        "- 制約付きジェネリクスの具体例を追加する",
        "- ユーティリティ型との関連を補足する",
      ].join("\n");

      const result = parseFeedbackBody(body);
      expect(result.roadmap).toBe("TypeScript / 型システム / ジェネリクス");
      expect(result.accuracy).toBe("ジェネリクスの説明は概ね正確です。");
      expect(result.suggestions).toEqual([
        "制約付きジェネリクスの具体例を追加する",
        "ユーティリティ型との関連を補足する",
      ]);
    });
  });

  describe("backend format (no bracket, heading/body separated)", () => {
    it("parses all three sections", () => {
      const body = [
        "反映先ロードマップ: TypeScript > 基礎 > ジェネリクス",
        "",
        "正確性チェック:",
        "ジェネリクスを型安全性の文脈で説明できており、大きな誤りはない。",
        "",
        "改善提案:",
        "- 関数だけでなくクラスやインターフェースにも適用できる点を追記する。",
        "- 型推論と明示的な型引数指定の違いを例で補う。",
      ].join("\n");

      const result = parseFeedbackBody(body);
      expect(result.roadmap).toBe("TypeScript > 基礎 > ジェネリクス");
      expect(result.accuracy).toBe(
        "ジェネリクスを型安全性の文脈で説明できており、大きな誤りはない。",
      );
      expect(result.suggestions).toEqual([
        "関数だけでなくクラスやインターフェースにも適用できる点を追記する。",
        "型推論と明示的な型引数指定の違いを例で補う。",
      ]);
    });

    it("parses body without roadmap section", () => {
      const body = [
        "正確性チェック:",
        "概要説明としては妥当だが、ネットワークや volume の観点が省略されている。",
        "",
        "改善提案:",
        "- service 間通信の説明を 1 文追加する。",
      ].join("\n");

      const result = parseFeedbackBody(body);
      expect(result.roadmap).toBeNull();
      expect(result.accuracy).toBe(
        "概要説明としては妥当だが、ネットワークや volume の観点が省略されている。",
      );
      expect(result.suggestions).toEqual([
        "service 間通信の説明を 1 文追加する。",
      ]);
    });
  });

  it("handles empty body", () => {
    const result = parseFeedbackBody("");
    expect(result.roadmap).toBeNull();
    expect(result.accuracy).toBeNull();
    expect(result.suggestions).toEqual([]);
  });

  it("handles full-width colon in suggestions header", () => {
    const body = "改善提案：\n- 項目A\n- 項目B";
    const result = parseFeedbackBody(body);
    expect(result.suggestions).toEqual(["項目A", "項目B"]);
  });

  it("handles accuracy only (inline format)", () => {
    const body = "正確性チェック: 正確に記述されています。";
    const result = parseFeedbackBody(body);
    expect(result.accuracy).toBe("正確に記述されています。");
    expect(result.suggestions).toEqual([]);
  });
});
