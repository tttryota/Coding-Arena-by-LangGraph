import { scoreLevel } from "./score";

describe("scoreLevel", () => {
  it.each([
    [null, "not_started"],
    [undefined, "not_started"],
    [0, "not_started"],
    [25, "not_started"],
    [26, "insufficient"],
    [50, "insufficient"],
    [51, "partial"],
    [75, "partial"],
    [76, "sufficient"],
    [100, "sufficient"],
  ])("score=%s → key=%s", (score, expectedKey) => {
    expect(scoreLevel(score as number | null | undefined).key).toBe(
      expectedKey,
    );
  });

  it("returns Japanese labels", () => {
    expect(scoreLevel(0).label).toBe("未着手");
    expect(scoreLevel(30).label).toBe("不十分");
    expect(scoreLevel(60).label).toBe("部分的");
    expect(scoreLevel(90).label).toBe("十分");
  });
});
