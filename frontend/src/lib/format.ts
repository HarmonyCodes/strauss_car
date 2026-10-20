// Display-only formatting; values are never recalculated on the client.
const shekel = (fractionDigits: number) =>
  new Intl.NumberFormat("he-IL", {
    style: "currency",
    currency: "ILS",
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  });

export function formatWhole(value: string): string {
  return shekel(0).format(Number(value));
}

export function formatDetailed(value: string): string {
  return shekel(2).format(Number(value));
}

const FIELD_LABELS: Record<string, string> = {
  occupation: "עיסוק",
  base_salary: "שכר בסיס",
  commissions: "עמלות",
  bonus: "בונוס",
  credit_points: "נקודות זיכוי",
  pension_rate: "שיעור הפרשה לפנסיה",
  study_fund_rate: "שיעור הפרשה לקרן השתלמות",
  children_under_23: "מספר ילדים מתחת לגיל 23",
  current: "החלופה הנוכחית",
  alternative: "החלופה החדשה",
};

export function fieldLabel(path: string): string {
  const root = path.split(".")[0];
  return FIELD_LABELS[root] ?? root;
}
