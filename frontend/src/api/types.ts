// Mirrors backend/app/api/schemas.py. Decimal values travel as strings.
export type Decimal = string;

export interface GroupOption {
  group: string;
  monthly_budget: Decimal;
}

export interface VehicleOption {
  vehicle_id: string;
  track: "regular" | "family";
  group: string | null;
  brand: string;
  model_name: string;
  registration_year: number;
  drive: string;
  is_electric: boolean;
  list_price: Decimal;
  monthly_use_value: Decimal;
  monthly_company_cost: Decimal;
  default_participation: Decimal;
}

export interface OccupationOption {
  name: string;
  group: string;
  car_mandatory: boolean;
  can_waive: boolean;
  waiver_maintenance: Decimal | null;
}

export interface OptionsResponse {
  rules_version: string;
  groups: GroupOption[];
  family_track: {
    min_children: number;
    child_age_limit_exclusive: number;
    vehicle_ids: string[];
  };
  vehicles: VehicleOption[];
  occupations: OccupationOption[];
  disclaimer: string;
}

export type CarChoice = { vehicle_id: string } | { waive: true };

export interface CompareRequest {
  occupation: string;
  base_salary: Decimal;
  commissions: Decimal;
  bonus: Decimal;
  credit_points: Decimal;
  pension_rate: Decimal;
  study_fund_rate: Decimal;
  children_under_23: number;
  current: CarChoice;
  alternative: CarChoice;
}

export interface ScenarioResult {
  vehicle_id: string | null;
  is_waiver: boolean;
  gross_salary: Decimal;
  use_value: Decimal;
  waiver_maintenance: Decimal;
  electric_net_bonus: Decimal;
  electric_gross_up: Decimal;
  taxable_income: Decimal;
  tax_before_credits: Decimal;
  credit_points_credit: Decimal;
  pension_credit: Decimal;
  income_tax: Decimal;
  national_insurance: Decimal;
  health_insurance: Decimal;
  pension_contribution: Decimal;
  study_fund_contribution: Decimal;
  participation: Decimal;
  net_before_electric_benefit: Decimal;
  net_salary: Decimal;
  net_salary_rounded: Decimal;
}

export interface CompareResponse {
  rules_version: string;
  tax_table_year: number;
  current: ScenarioResult;
  alternative: ScenarioResult;
  net_difference: Decimal;
  net_difference_rounded: Decimal;
  assumptions: string[];
  disclaimer: string;
}
