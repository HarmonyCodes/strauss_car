import { describe, expect, it } from "vitest";
import { percentToRate } from "../lib/percent";

describe("percentToRate", () => {
  it.each([
    ["6", "0.06"],
    ["5.5", "0.055"],
    ["0", "0"],
    ["100", "1"],
    ["12.50", "0.125"],
    ["0.1", "0.001"],
    ["7.1234", "0.071234"],
  ])("converts %s%% to %s", (input, expected) => {
    expect(percentToRate(input)).toBe(expected);
  });

  it.each(["", "abc", "-1", "1,5", "1e2"])("rejects %j", (input) => {
    expect(percentToRate(input)).toBeNull();
  });
});
