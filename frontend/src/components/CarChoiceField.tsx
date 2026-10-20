import type { VehicleOption } from "../api/types";

export interface ChoiceState {
  mode: "vehicle" | "waive";
  vehicleId: string;
}

interface Props {
  legend: string;
  idPrefix: string;
  vehicles: VehicleOption[];
  canWaive: boolean;
  value: ChoiceState;
  onChange: (value: ChoiceState) => void;
}

export function CarChoiceField({
  legend,
  idPrefix,
  vehicles,
  canWaive,
  value,
  onChange,
}: Props) {
  const selected = vehicles.find((v) => v.vehicle_id === value.vehicleId);
  return (
    <fieldset className="rounded-lg border border-slate-300 bg-white p-4">
      <legend className="px-2 font-semibold">{legend}</legend>
      <div className="flex flex-wrap gap-4">
        <label className="flex items-center gap-2">
          <input
            type="radio"
            name={`${idPrefix}-mode`}
            checked={value.mode === "vehicle"}
            onChange={() => onChange({ ...value, mode: "vehicle" })}
          />
          רכב
        </label>
        <label className="flex items-center gap-2">
          <input
            type="radio"
            name={`${idPrefix}-mode`}
            checked={value.mode === "waive"}
            disabled={!canWaive}
            onChange={() => onChange({ ...value, mode: "waive" })}
          />
          ויתור על רכב
        </label>
      </div>
      {!canWaive && (
        <p className="mt-1 text-sm text-slate-600">
          ויתור על רכב אינו אפשרי לעיסוק שנבחר.
        </p>
      )}
      {value.mode === "vehicle" && (
        <div className="mt-3">
          <label htmlFor={`${idPrefix}-vehicle`} className="block text-sm font-medium">
            בחירת רכב
          </label>
          <select
            id={`${idPrefix}-vehicle`}
            className="mt-1 w-full rounded border border-slate-400 bg-white p-2"
            value={value.vehicleId}
            onChange={(e) => onChange({ ...value, vehicleId: e.target.value })}
          >
            <option value="">בחרו רכב…</option>
            {vehicles.map((v) => (
              <option key={v.vehicle_id} value={v.vehicle_id}>
                {`${v.vehicle_id} — ${v.brand} ${v.model_name} (${v.track === "family" ? "משפחתי" : `קבוצה ${v.group}`})`}
              </option>
            ))}
          </select>
          {selected && (
            <p className="mt-1 text-sm text-slate-600">
              {`${selected.drive} · שנת רישום ${selected.registration_year}${selected.is_electric ? " · חשמלי" : ""}`}
            </p>
          )}
        </div>
      )}
    </fieldset>
  );
}
