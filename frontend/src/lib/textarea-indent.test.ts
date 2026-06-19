import { describe, expect, it } from "vitest";

import { applyTextareaIndent } from "./textarea-indent";

describe("applyTextareaIndent", () => {
  it("inserts indentation at the cursor", () => {
    const result = applyTextareaIndent("ab", 1, 1);

    expect(result.value).toBe("a  b");
    expect(result.selectionStart).toBe(3);
    expect(result.selectionEnd).toBe(3);
  });

  it("indents multiple selected lines", () => {
    const result = applyTextareaIndent("a\nb", 0, 3);

    expect(result.value).toBe("  a\n  b");
    expect(result.selectionStart).toBe(2);
    expect(result.selectionEnd).toBe(7);
  });

  it("outdents multiple lines by one level", () => {
    const result = applyTextareaIndent("  a\n  b", 2, 7, {
      outdent: true,
    });

    expect(result.value).toBe("a\nb");
    expect(result.selectionStart).toBe(0);
    expect(result.selectionEnd).toBe(3);
  });
});
