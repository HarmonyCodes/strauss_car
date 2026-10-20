const DECIMAL = /^\d+(\.\d+)?$/;

// Converts a percentage string ("5.5") to a fraction string ("0.055") by
// shifting the decimal point, avoiding float arithmetic. Returns null if invalid.
export function percentToRate(input: string): string | null {
  const text = input.trim();
  if (!DECIMAL.test(text)) return null;
  const [intPart, fracPart = ""] = text.split(".");
  const digits = intPart.padStart(2, "0") + fracPart;
  const splitAt = digits.length - fracPart.length - 2;
  const whole = digits.slice(0, splitAt).replace(/^0+(?=\d)/, "") || "0";
  const frac = digits.slice(splitAt).replace(/0+$/, "");
  return frac ? `${whole}.${frac}` : whole;
}
