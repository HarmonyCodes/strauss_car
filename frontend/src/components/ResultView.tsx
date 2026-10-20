import type { CompareResponse, ScenarioResult } from "../api/types";
import { formatDetailed, formatWhole } from "../lib/format";

const ROWS: { label: string; key: keyof ScenarioResult; hideIfZero?: boolean }[] = [
  { label: "שכר ברוטו", key: "gross_salary" },
  { label: "שווי שימוש ברכב", key: "use_value" },
  { label: "אחזקת רכב (ויתור)", key: "waiver_maintenance", hideIfZero: true },
  { label: "הכנסה חייבת", key: "taxable_income" },
  { label: "מס הכנסה לפני זיכויים", key: "tax_before_credits" },
  { label: "זיכוי נקודות זיכוי", key: "credit_points_credit" },
  { label: "זיכוי פנסיה", key: "pension_credit" },
  { label: "מס הכנסה", key: "income_tax" },
  { label: "ביטוח לאומי", key: "national_insurance" },
  { label: "ביטוח בריאות", key: "health_insurance" },
  { label: "הפרשה לפנסיה", key: "pension_contribution" },
  { label: "הפרשה לקרן השתלמות", key: "study_fund_contribution" },
  { label: "השתתפות עובד ברכב", key: "participation" },
  { label: "גילום (הטבת רכב חשמלי)", key: "electric_gross_up", hideIfZero: true },
  { label: "הטבת רכב חשמלי נטו", key: "electric_net_bonus", hideIfZero: true },
  { label: "נטו לפני הטבת חשמלי", key: "net_before_electric_benefit" },
];

function title(s: ScenarioResult): string {
  return s.is_waiver ? "ויתור על רכב" : `רכב ${s.vehicle_id}`;
}

export function ResultView({ result }: { result: CompareResponse }) {
  const diff = Number(result.net_difference);
  const diffText =
    diff > 0 ? "החלופה החדשה גבוהה יותר" : diff < 0 ? "החלופה החדשה נמוכה יותר" : "אין הבדל";
  const rows = ROWS.filter(
    (r) =>
      !r.hideIfZero ||
      Number(result.current[r.key]) !== 0 ||
      Number(result.alternative[r.key]) !== 0,
  );

  return (
    <section aria-labelledby="result-heading" className="space-y-4">
      <h2 id="result-heading" className="text-xl font-bold">
        תוצאות ההשוואה
      </h2>
      <div className="grid gap-3 sm:grid-cols-3">
        <Headline label={`נטו — נוכחית (${title(result.current)})`} value={formatWhole(result.current.net_salary_rounded)} />
        <Headline label={`נטו — חדשה (${title(result.alternative)})`} value={formatWhole(result.alternative.net_salary_rounded)} />
        <Headline label="הפרש נטו (חדשה פחות נוכחית)" value={formatWhole(result.net_difference_rounded)} note={diffText} strong />
      </div>

      <div className="overflow-x-auto rounded-lg border border-slate-300 bg-white">
        <table className="w-full text-sm">
          <caption className="p-2 text-start font-semibold">פירוט רכיבי החישוב (לחודש)</caption>
          <thead className="bg-slate-100">
            <tr>
              <th scope="col" className="p-2 text-start">רכיב</th>
              <th scope="col" className="p-2 text-start">נוכחית</th>
              <th scope="col" className="p-2 text-start">חדשה</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.key} className="border-t border-slate-200">
                <th scope="row" className="p-2 text-start font-normal">{r.label}</th>
                <td className="p-2">{formatDetailed(String(result.current[r.key]))}</td>
                <td className="p-2">{formatDetailed(String(result.alternative[r.key]))}</td>
              </tr>
            ))}
            <tr className="border-t-2 border-slate-400 font-bold">
              <th scope="row" className="p-2 text-start">שכר נטו</th>
              <td className="p-2">{formatDetailed(result.current.net_salary)}</td>
              <td className="p-2">{formatDetailed(result.alternative.net_salary)}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <p className="text-sm text-slate-600">
        {`גרסת כללים: ${result.rules_version} · שנת מס: ${result.tax_table_year}`}
      </p>

      {result.assumptions.length > 0 && (
        <div>
          <h3 className="font-semibold">הנחות ואזהרות</h3>
          <ul dir="ltr" className="list-disc ps-5 text-start text-sm">
            {result.assumptions.map((a) => (
              <li key={a}>{a}</li>
            ))}
          </ul>
        </div>
      )}

      <p role="note" className="rounded border border-amber-400 bg-amber-50 p-3 text-sm">
        {result.disclaimer}
      </p>
    </section>
  );
}

function Headline({ label, value, note, strong }: { label: string; value: string; note?: string; strong?: boolean }) {
  return (
    <div className={`rounded-lg border p-3 ${strong ? "border-blue-700 bg-blue-50" : "border-slate-300 bg-white"}`}>
      <div className="text-sm text-slate-700">{label}</div>
      <div className="text-2xl font-bold">{value}</div>
      {note && <div className="text-sm">{note}</div>}
    </div>
  );
}
