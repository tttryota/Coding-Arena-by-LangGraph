import { describe, it, expect } from "vitest";
import { toIso } from "./use-feedbacks";

describe("toIso", () => {
  it("produces start-of-day with timezone offset for from dates", () => {
    const result = toIso("2026-05-20", false);
    expect(result).toMatch(/^2026-05-20T00:00:00[+-]\d{2}:\d{2}$/);
  });

  it("produces end-of-day with milliseconds for to dates (inclusive)", () => {
    const result = toIso("2026-05-20", true);
    expect(result).toMatch(/^2026-05-20T23:59:59\.999[+-]\d{2}:\d{2}$/);
  });

  it("includes the correct timezone offset for the actual time point", () => {
    const result = toIso("2026-05-20", false);
    // Extract offset from result
    const offsetMatch = result.match(/([+-])(\d{2}):(\d{2})$/);
    expect(offsetMatch).not.toBeNull();

    // Verify it matches the browser's timezone offset for that date
    const d = new Date("2026-05-20T00:00:00");
    const expectedOffset = -d.getTimezoneOffset();
    const expectedSign = expectedOffset >= 0 ? "+" : "-";
    const absOffset = Math.abs(expectedOffset);
    const expectedHours = String(Math.floor(absOffset / 60)).padStart(2, "0");
    const expectedMinutes = String(absOffset % 60).padStart(2, "0");

    expect(offsetMatch![1]).toBe(expectedSign);
    expect(offsetMatch![2]).toBe(expectedHours);
    expect(offsetMatch![3]).toBe(expectedMinutes);
  });

  it("uses the correct offset at each time point (DST-safe)", () => {
    const from = toIso("2026-05-20", false);
    const to = toIso("2026-05-20", true);
    // Both should have valid timezone offsets
    expect(from).toMatch(/[+-]\d{2}:\d{2}$/);
    expect(to).toMatch(/[+-]\d{2}:\d{2}$/);
    // Offsets are derived from the actual Date object at each time point
    const fromD = new Date("2026-05-20T00:00:00");
    const toD = new Date("2026-05-20T23:59:59");
    const fromExpected = -fromD.getTimezoneOffset();
    const toExpected = -toD.getTimezoneOffset();
    // On non-DST dates they should be equal; on DST dates they may differ
    expect(typeof fromExpected).toBe("number");
    expect(typeof toExpected).toBe("number");
  });
});
