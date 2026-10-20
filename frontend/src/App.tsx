import { useEffect, useMemo, useState, type FormEvent } from "react";
import { ApiError, compareScenarios, getOptions } from "./api/client";
import type { CarChoice, CompareRequest, CompareResponse, OptionsResponse } from "./api/types";
import { CarChoiceField, type ChoiceState } from "./components/CarChoiceField";
import { ResultView } from "./components/ResultView";
import { fieldLabel } from "./lib/format";
import { percentToRate } from "./lib/percent";

interface FormState {
  occupation: string;
  base_salary: string;
  commissions: string;
  bonus: string;
  credit_points: string;
  pension_percent: string;
  study_fund_percent: string;
  children_under_23: string;
}

const INITIAL_FORM: FormState = {
  occupation: "",
  base_salary: "",
  commissions: "0",
  bonus: "0",
  credit_points: "",
  pension_percent: "",
  study_fund_percent: "",
  children_under_23: "0",
};

const EMPTY_CHOICE: ChoiceState = { mode: "vehicle", vehicleId: "" };
const NUMBER = /^\d+(\.\d+)?$/;
const INTEGER = /^-?\d+$/;

function toChoice(c: ChoiceState): CarChoice | null {
  if (c.mode === "waive") return { waive: true };
  return c.vehicleId ? { vehicle_id: c.vehicleId } : null;
}

// Format-only checks; ranges and eligibility are enforced by the server.
function buildRequest(
  form: FormState,
  current: ChoiceState,
  alternative: ChoiceState,
): { request?: CompareRequest; errors: string[] } {
  const errors: string[] = [];
  if (!form.occupation) errors.push("יש לבחור עיסוק");
  const money = (value: string, label: string) => {
    if (!NUMBER.test(value.trim())) errors.push(`${label}: יש להזין מספר חיובי או אפס`);
    return value.trim();
  };
  const base_salary = money(form.base_salary, "שכר בסיס");
  const commissions = money(form.commissions, "עמלות");
  const bonus = money(form.bonus, "בונוס");
  const credit_points = money(form.credit_points, "נקודות זיכוי");
  const pension_rate = percentToRate(form.pension_percent);
  if (pension_rate === null) errors.push("שיעור הפרשה לפנסיה: יש להזין אחוז");
  const study_fund_rate = percentToRate(form.study_fund_percent);
  if (study_fund_rate === null) errors.push("שיעור הפרשה לקרן השתלמות: יש להזין אחוז");
  if (!INTEGER.test(form.children_under_23.trim())) errors.push("מספר ילדים מתחת לגיל 23: יש להזין מספר שלם");
  const cur = toChoice(current);
  if (!cur) errors.push("יש לבחור רכב או ויתור בחלופה הנוכחית");
  const alt = toChoice(alternative);
  if (!alt) errors.push("יש לבחור רכב או ויתור בחלופה החדשה");
  if (errors.length > 0 || !cur || !alt || pension_rate === null || study_fund_rate === null) {
    return { errors };
  }
  return {
    errors,
    request: {
      occupation: form.occupation,
      base_salary,
      commissions,
      bonus,
      credit_points,
      pension_rate,
      study_fund_rate,
      children_under_23: Number(form.children_under_23.trim()),
      current: cur,
      alternative: alt,
    },
  };
}

export default function App() {
  const [options, setOptions] = useState<OptionsResponse | null>(null);
  const [optionsError, setOptionsError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const [form, setForm] = useState<FormState>(INITIAL_FORM);
  const [current, setCurrent] = useState<ChoiceState>(EMPTY_CHOICE);
  const [alternative, setAlternative] = useState<ChoiceState>(EMPTY_CHOICE);

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<CompareResponse | null>(null);
  const [errors, setErrors] = useState<string[]>([]);
  const [errorKind, setErrorKind] = useState<"form" | "validation" | "business" | "server" | "network" | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setOptionsError(null);
    getOptions(controller.signal)
      .then(setOptions)
      .catch((e: unknown) => {
        if (controller.signal.aborted) return;
        setOptionsError(e instanceof ApiError ? e.message : "טעינת האפשרויות נכשלה");
      });
    return () => controller.abort();
  }, [reloadKey]);

  const occupation = useMemo(
    () => options?.occupations.find((o) => o.name === form.occupation),
    [options, form.occupation],
  );
  const canWaive = occupation?.can_waive ?? false;

  const setField = (key: keyof FormState) => (e: { target: { value: string } }) =>
    setForm((f) => ({ ...f, [key]: e.target.value }));

  const onOccupationChange = (name: string) => {
    setForm((f) => ({ ...f, occupation: name }));
    const waivable = options?.occupations.find((o) => o.name === name)?.can_waive ?? false;
    if (!waivable) {
      const reset = (c: ChoiceState): ChoiceState => (c.mode === "waive" ? { ...c, mode: "vehicle" } : c);
      setCurrent(reset);
      setAlternative(reset);
    }
  };

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setResult(null);
    const built = buildRequest(form, current, alternative);
    if (!built.request) {
      setErrors(built.errors);
      setErrorKind("form");
      return;
    }
    setErrors([]);
    setErrorKind(null);
    setLoading(true);
    try {
      setResult(await compareScenarios(built.request));
    } catch (err) {
      if (err instanceof ApiError) {
        setErrorKind(err.kind);
        setErrors(
          err.kind === "validation"
            ? err.fieldErrors.map((fe) => `${fieldLabel(fe.field)}: ${fe.message}`)
            : [err.message],
        );
      } else {
        setErrorKind("server");
        setErrors(["אירעה שגיאה לא צפויה"]);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="mx-auto max-w-4xl space-y-6 p-4">
      <header>
        <h1 className="text-2xl font-bold">יועץ הרכב של שטראוס</h1>
        <p className="text-slate-700">השוואת השפעת בחירת הרכב על שכר הנטו.</p>
      </header>

      {optionsError && (
        <div role="alert" className="rounded border border-red-500 bg-red-50 p-3">
          <p>{optionsError}</p>
          <button type="button" className="mt-2 rounded border border-red-700 px-3 py-1" onClick={() => setReloadKey((k) => k + 1)}>
            נסו שוב
          </button>
        </div>
      )}
      {!options && !optionsError && <p role="status">טוען אפשרויות…</p>}

      {options && (
        <form onSubmit={onSubmit} noValidate className="space-y-4" aria-busy={loading}>
          <fieldset className="grid gap-3 rounded-lg border border-slate-300 bg-white p-4 sm:grid-cols-2">
            <legend className="px-2 font-semibold">נתוני עובד (נתוני בדיקה בלבד)</legend>
            <Field label="עיסוק" id="occupation" wide>
              <select id="occupation" className="w-full rounded border border-slate-400 bg-white p-2" value={form.occupation} onChange={(e) => onOccupationChange(e.target.value)}>
                <option value="">בחרו עיסוק…</option>
                {options.occupations.map((o) => (
                  <option key={o.name} value={o.name}>{o.name}</option>
                ))}
              </select>
            </Field>
            <Field label="שכר בסיס חודשי (₪)" id="base_salary">
              <input id="base_salary" inputMode="decimal" className="w-full rounded border border-slate-400 p-2" value={form.base_salary} onChange={setField("base_salary")} />
            </Field>
            <Field label="עמלות (₪)" id="commissions">
              <input id="commissions" inputMode="decimal" className="w-full rounded border border-slate-400 p-2" value={form.commissions} onChange={setField("commissions")} />
            </Field>
            <Field label="בונוס (₪)" id="bonus">
              <input id="bonus" inputMode="decimal" className="w-full rounded border border-slate-400 p-2" value={form.bonus} onChange={setField("bonus")} />
            </Field>
            <Field label="נקודות זיכוי" id="credit_points">
              <input id="credit_points" inputMode="decimal" className="w-full rounded border border-slate-400 p-2" value={form.credit_points} onChange={setField("credit_points")} />
            </Field>
            <Field label="שיעור הפרשה לפנסיה (%)" id="pension_percent">
              <input id="pension_percent" inputMode="decimal" className="w-full rounded border border-slate-400 p-2" value={form.pension_percent} onChange={setField("pension_percent")} />
            </Field>
            <Field label="שיעור הפרשה לקרן השתלמות (%)" id="study_fund_percent">
              <input id="study_fund_percent" inputMode="decimal" className="w-full rounded border border-slate-400 p-2" value={form.study_fund_percent} onChange={setField("study_fund_percent")} />
            </Field>
            <Field label="מספר ילדים מתחת לגיל 23" id="children_under_23">
              <input id="children_under_23" inputMode="numeric" className="w-full rounded border border-slate-400 p-2" value={form.children_under_23} onChange={setField("children_under_23")} />
            </Field>
          </fieldset>

          <div className="grid gap-4 md:grid-cols-2">
            <CarChoiceField legend="חלופה נוכחית" idPrefix="current" vehicles={options.vehicles} canWaive={canWaive} value={current} onChange={setCurrent} />
            <CarChoiceField legend="חלופה חדשה" idPrefix="alternative" vehicles={options.vehicles} canWaive={canWaive} value={alternative} onChange={setAlternative} />
          </div>

          {errors.length > 0 && (
            <div role="alert" className="rounded border border-red-500 bg-red-50 p-3">
              <p className="font-semibold">
                {errorKind === "network" ? "כשל תקשורת" : errorKind === "business" ? "לא ניתן לבצע את ההשוואה" : errorKind === "server" ? "שגיאת שרת" : "יש לתקן את הנתונים"}
              </p>
              <ul className="list-disc ps-5">
                {errors.map((m, i) => (
                  <li key={i} dir={errorKind === "business" || errorKind === "validation" ? "auto" : undefined}>{m}</li>
                ))}
              </ul>
            </div>
          )}

          <button type="submit" disabled={loading} className="w-full rounded bg-blue-700 px-4 py-3 font-semibold text-white disabled:opacity-60 sm:w-auto">
            {loading ? "מחשב…" : "השוואה"}
          </button>
        </form>
      )}

      {loading && <p role="status">מחשב השוואה…</p>}
      {result && <ResultView result={result} />}
      {options && !result && (
        <p className="text-sm text-slate-600">{options.disclaimer}</p>
      )}
    </main>
  );
}

function Field({ label, id, wide, children }: { label: string; id: string; wide?: boolean; children: React.ReactNode }) {
  return (
    <div className={wide ? "sm:col-span-2" : undefined}>
      <label htmlFor={id} className="mb-1 block text-sm font-medium">{label}</label>
      {children}
    </div>
  );
}
