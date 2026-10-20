import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "../App";
import type { CompareResponse, OptionsResponse, ScenarioResult } from "../api/types";

const OPTIONS: OptionsResponse = {
  rules_version: "test-rules",
  groups: [{ group: "ב", monthly_budget: "3700" }],
  family_track: { min_children: 4, child_age_limit_exclusive: 23, vehicle_ids: [] },
  vehicles: [
    { vehicle_id: "CAR-01", track: "regular", group: "ב", brand: "BrandA", model_name: "ModelA", registration_year: 2025, drive: "בנזין", is_electric: false, list_price: "100000", monthly_use_value: "400", monthly_company_cost: "3000", default_participation: "50" },
    { vehicle_id: "CAR-02", track: "regular", group: "ב", brand: "BrandB", model_name: "ModelB", registration_year: 2025, drive: "חשמלי", is_electric: true, list_price: "120000", monthly_use_value: "500", monthly_company_cost: "3200", default_participation: "60" },
  ],
  occupations: [
    { name: "עיסוק גמיש", group: "ב", car_mandatory: false, can_waive: true, waiver_maintenance: "1500" },
    { name: "עיסוק חובה", group: "ב", car_mandatory: true, can_waive: false, waiver_maintenance: null },
  ],
  disclaimer: "נתוני המחשה בלבד",
};

function scenario(id: string | null, net: string, rounded: string): ScenarioResult {
  return {
    vehicle_id: id, is_waiver: id === null,
    gross_salary: "10000", use_value: "400", waiver_maintenance: "0",
    electric_net_bonus: "0", electric_gross_up: "0", taxable_income: "10400",
    tax_before_credits: "1000", credit_points_credit: "200", pension_credit: "50",
    income_tax: "750", national_insurance: "300", health_insurance: "200",
    pension_contribution: "600", study_fund_contribution: "250", participation: "50",
    net_before_electric_benefit: net, net_salary: net, net_salary_rounded: rounded,
  };
}

const RESULT: CompareResponse = {
  rules_version: "test-rules", tax_table_year: 2026,
  current: scenario("CAR-01", "8000.5", "8001"),
  alternative: scenario("CAR-02", "8100.25", "8100"),
  net_difference: "99.75", net_difference_rounded: "100",
  assumptions: ["Illustrative assumption"],
  disclaimer: "תוצאה להמחשה בלבד",
};

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

let fetchMock: ReturnType<typeof vi.fn>;

beforeEach(() => {
  fetchMock = vi.fn();
  vi.stubGlobal("fetch", fetchMock);
});
afterEach(() => vi.unstubAllGlobals());

async function fillForm(user: ReturnType<typeof userEvent.setup>, occupation = "עיסוק גמיש") {
  await user.selectOptions(await screen.findByLabelText("עיסוק"), occupation);
  await user.type(screen.getByLabelText("שכר בסיס חודשי (₪)"), "10000");
  await user.type(screen.getByLabelText("נקודות זיכוי"), "2.25");
  await user.type(screen.getByLabelText("שיעור הפרשה לפנסיה (%)"), "6");
  await user.type(screen.getByLabelText("שיעור הפרשה לקרן השתלמות (%)"), "2.5");
  const groups = screen.getAllByRole("group");
  const currentGroup = groups.find((g) => within(g).queryByText("חלופה נוכחית"))!;
  const altGroup = groups.find((g) => within(g).queryByText("חלופה חדשה"))!;
  await user.selectOptions(within(currentGroup).getByLabelText("בחירת רכב"), "CAR-01");
  await user.selectOptions(within(altGroup).getByLabelText("בחירת רכב"), "CAR-02");
}

describe("App", () => {
  it("loads options from the API and shows an error with retry when loading fails", async () => {
    fetchMock.mockRejectedValueOnce(new TypeError("down")).mockResolvedValueOnce(jsonResponse(OPTIONS));
    const user = userEvent.setup();
    render(<App />);
    expect(await screen.findByText(/לא ניתן להתחבר לשרת/)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "נסו שוב" }));
    expect(await screen.findByLabelText("עיסוק")).toBeInTheDocument();
    expect(fetchMock.mock.calls[0][0]).toBe("/api/v1/options");
  });

  it("sends the expected payload and shows net amounts and the difference", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(OPTIONS)).mockResolvedValueOnce(jsonResponse(RESULT));
    const user = userEvent.setup();
    render(<App />);
    await fillForm(user);
    await user.click(screen.getByRole("button", { name: "השוואה" }));

    const heading = await screen.findByRole("heading", { name: "תוצאות ההשוואה" });
    expect(heading).toBeInTheDocument();
    expect(screen.getByText("החלופה החדשה גבוהה יותר")).toBeInTheDocument();
    expect(screen.getByText("Illustrative assumption")).toBeInTheDocument();
    expect(screen.getByText("תוצאה להמחשה בלבד")).toBeInTheDocument();

    const [url, init] = fetchMock.mock.calls[1];
    expect(url).toBe("/api/v1/scenarios/compare");
    expect(JSON.parse(init.body as string)).toEqual({
      occupation: "עיסוק גמיש",
      base_salary: "10000",
      commissions: "0",
      bonus: "0",
      credit_points: "2.25",
      pension_rate: "0.06",
      study_fund_rate: "0.025",
      children_under_23: 0,
      current: { vehicle_id: "CAR-01" },
      alternative: { vehicle_id: "CAR-02" },
    });
  });

  it("sends a waiver choice when the occupation allows it", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(OPTIONS)).mockResolvedValueOnce(jsonResponse(RESULT));
    const user = userEvent.setup();
    render(<App />);
    await fillForm(user);
    const altGroup = screen.getAllByRole("group").find((g) => within(g).queryByText("חלופה חדשה"))!;
    await user.click(within(altGroup).getByLabelText("ויתור על רכב"));
    await user.click(screen.getByRole("button", { name: "השוואה" }));
    await screen.findByRole("heading", { name: "תוצאות ההשוואה" });
    expect(JSON.parse(fetchMock.mock.calls[1][1].body as string).alternative).toEqual({ waive: true });
  });

  it("disables waiving for an occupation that cannot waive", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(OPTIONS));
    const user = userEvent.setup();
    render(<App />);
    await user.selectOptions(await screen.findByLabelText("עיסוק"), "עיסוק חובה");
    for (const radio of screen.getAllByLabelText("ויתור על רכב")) {
      expect(radio).toBeDisabled();
    }
  });

  it("blocks submission with clear messages when required input is missing", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(OPTIONS));
    const user = userEvent.setup();
    render(<App />);
    await screen.findByLabelText("עיסוק");
    await user.click(screen.getByRole("button", { name: "השוואה" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("יש לבחור עיסוק");
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("shows server validation errors (422) with Hebrew field names", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(OPTIONS)).mockResolvedValueOnce(
      jsonResponse({ detail: [{ loc: ["body", "children_under_23"], msg: "Input should be greater than or equal to 0", type: "greater_than_equal" }] }, 422),
    );
    const user = userEvent.setup();
    render(<App />);
    await fillForm(user);
    await user.clear(screen.getByLabelText("מספר ילדים מתחת לגיל 23"));
    await user.type(screen.getByLabelText("מספר ילדים מתחת לגיל 23"), "-1");
    await user.click(screen.getByRole("button", { name: "השוואה" }));
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("מספר ילדים מתחת לגיל 23");
    expect(JSON.parse(fetchMock.mock.calls[1][1].body as string).children_under_23).toBe(-1);
  });

  it("shows the business error message returned by the server", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(OPTIONS)).mockResolvedValueOnce(
      jsonResponse({ error: { code: "invalid_scenario", message: "Family-track eligibility conditions are not met for CAR-19" } }, 422),
    );
    const user = userEvent.setup();
    render(<App />);
    await fillForm(user);
    await user.click(screen.getByRole("button", { name: "השוואה" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Family-track eligibility conditions are not met for CAR-19");
    expect(screen.queryByRole("heading", { name: "תוצאות ההשוואה" })).not.toBeInTheDocument();
  });

  it("shows a generic message for server errors and for network failure", async () => {
    fetchMock
      .mockResolvedValueOnce(jsonResponse(OPTIONS))
      .mockResolvedValueOnce(jsonResponse({ error: { code: "internal_error", message: "internal" } }, 500))
      .mockRejectedValueOnce(new TypeError("down"));
    const user = userEvent.setup();
    render(<App />);
    await fillForm(user);
    await user.click(screen.getByRole("button", { name: "השוואה" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("שגיאה בשרת");
    await user.click(screen.getByRole("button", { name: "השוואה" }));
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("כשל תקשורת"));
  });

  it("does not persist form data in browser storage", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(OPTIONS)).mockResolvedValueOnce(jsonResponse(RESULT));
    const user = userEvent.setup();
    render(<App />);
    await fillForm(user);
    await user.click(screen.getByRole("button", { name: "השוואה" }));
    await screen.findByRole("heading", { name: "תוצאות ההשוואה" });
    expect(localStorage.length).toBe(0);
    expect(sessionStorage.length).toBe(0);
  });
});
