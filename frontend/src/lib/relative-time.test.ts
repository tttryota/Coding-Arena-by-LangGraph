import { describe, it, expect, vi, afterEach } from "vitest";
import { formatRelativeTime } from "./relative-time";

const NOW = new Date("2026-05-25T12:00:00Z").getTime();

describe("formatRelativeTime", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(NOW);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("returns — for null", () => {
    expect(formatRelativeTime(null)).toBe("—");
  });

  it("returns — for undefined", () => {
    expect(formatRelativeTime(undefined)).toBe("—");
  });

  it("returns — for invalid date string", () => {
    expect(formatRelativeTime("not-a-date")).toBe("—");
  });

  it("returns — for future dates", () => {
    expect(formatRelativeTime("2026-05-26T12:00:00Z")).toBe("—");
  });

  it("returns たった今 for < 1 minute", () => {
    expect(formatRelativeTime("2026-05-25T11:59:30Z")).toBe("たった今");
  });

  it("returns N分前 for < 1 hour", () => {
    expect(formatRelativeTime("2026-05-25T11:30:00Z")).toBe("30分前");
  });

  it("returns 1分前 at exactly 1 minute", () => {
    expect(formatRelativeTime("2026-05-25T11:59:00Z")).toBe("1分前");
  });

  it("returns N時間前 for < 24 hours", () => {
    expect(formatRelativeTime("2026-05-25T09:00:00Z")).toBe("3時間前");
  });

  it("returns 1時間前 at exactly 1 hour", () => {
    expect(formatRelativeTime("2026-05-25T11:00:00Z")).toBe("1時間前");
  });

  it("returns 昨日 for 24-48 hours", () => {
    expect(formatRelativeTime("2026-05-24T12:00:00Z")).toBe("昨日");
  });

  it("returns N日前 for 2-7 days", () => {
    expect(formatRelativeTime("2026-05-22T12:00:00Z")).toBe("3日前");
  });

  it("returns 2日前 at exactly 2 days", () => {
    expect(formatRelativeTime("2026-05-23T12:00:00Z")).toBe("2日前");
  });

  it("returns absolute date for >= 7 days", () => {
    const result = formatRelativeTime("2026-05-10T14:30:00Z");
    // Intl.DateTimeFormat with ja-JP produces locale-specific format
    expect(result).toMatch(/2026/);
    expect(result).toMatch(/05/);
    expect(result).toMatch(/10/);
  });
});
