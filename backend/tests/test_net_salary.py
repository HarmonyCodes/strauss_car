from decimal import Decimal

import pytest

from app.domain.errors import DomainValidationError, UnsupportedRuleError
from app.domain.models import DriveType, VehicleTrack
from app.domain.net_salary import calculate_scenario, compare_scenarios
from app.domain.rounding import round_to_shekel
from app.domain.rules import RulesConfig
from app.domain.scenario import CarSelection, EmployeeProfile, SalaryComponents
from tests.helpers import make_employee, make_occupation, make_vehicle

D = Decimal
TOLERANCE = D("1e-25")


def regular_car(**overrides: object):  # noqa: ANN201
    fields: dict[str, object] = {"monthly_use_value": D(400), "default_participation": D(50)}
    fields.update(overrides)
    return make_vehicle(**fields)


def family_car():  # noqa: ANN201
    return make_vehicle(
        vehicle_id="V-FAM",
        track=VehicleTrack.FAMILY,
        group=None,
        monthly_use_value=D(500),
        monthly_company_cost=D(1800),
        default_participation=D(999),
    )


def test_regular_car_breakdown(synthetic_rules: RulesConfig) -> None:
    result = calculate_scenario(make_employee(), CarSelection.of(regular_car()), synthetic_rules)
    assert result.taxable_income == D(3400)
    assert result.tax_before_credits == D(720)  # 100 + 200 + 1400 * 0.3
    assert result.credit_points_credit == D(200)
    assert result.pension_credit == D("22.05")
    assert result.income_tax == D("497.95")
    assert result.national_insurance == D(150)
    assert result.health_insurance == D(126)
    assert result.pension_contribution == D(180)
    assert result.study_fund_contribution == D("75")
    assert result.participation == D(50)
    assert result.net_salary == D("1921.05")
    assert result.electric_gross_up == 0
    assert result.rules_version == "test-1"
    assert result.tax_table_year == 2025
    assert result.assumptions


def test_use_value_affects_tax_and_social_bases(synthetic_rules: RulesConfig) -> None:
    employee = make_employee()
    with_value = calculate_scenario(employee, CarSelection.of(regular_car()), synthetic_rules)
    without = calculate_scenario(
        employee, CarSelection.of(regular_car(monthly_use_value=D(0))), synthetic_rules
    )
    assert without.net_salary == D("2077.05")
    assert without.net_salary - with_value.net_salary == D(156)
    assert without.taxable_income == D(3000)


def test_waiver_adds_taxable_maintenance(synthetic_rules: RulesConfig) -> None:
    result = calculate_scenario(make_employee(), CarSelection.waiver(), synthetic_rules)
    assert result.is_waiver
    assert result.vehicle_id is None
    assert result.use_value == 0
    assert result.participation == 0
    assert result.waiver_maintenance == D(1200)
    assert result.taxable_income == D(4200)
    assert result.income_tax == D("737.95")
    assert result.national_insurance == D(190)
    assert result.health_insurance == D(158)
    assert result.net_salary == D("2859.05")


def test_waiver_rejected_when_occupation_cannot_waive(synthetic_rules: RulesConfig) -> None:
    employee = make_employee(can_waive=False, car_mandatory=True, waiver_maintenance=D(0))
    with pytest.raises(DomainValidationError, match="waive"):
        calculate_scenario(employee, CarSelection.waiver(), synthetic_rules)


def test_family_participation_adds_gap_share_to_default(synthetic_rules: RulesConfig) -> None:
    employee = make_employee(children_under_23=4)
    result = calculate_scenario(employee, CarSelection.of(family_car()), synthetic_rules)
    # default 999 + 0.5 * (1800 - 1000) = 1399
    assert result.participation == D(1399)
    assert result.use_value == D(500)
    # Same as the earlier hand-derived net with participation 400, minus the extra 999.
    assert result.net_salary == D("533.05")


def test_family_car_rejected_without_enough_children(synthetic_rules: RulesConfig) -> None:
    employee = make_employee(children_under_23=3, group="ג")
    with pytest.raises(DomainValidationError, match="Family-track eligibility") as error:
        calculate_scenario(employee, CarSelection.of(family_car()), synthetic_rules)
    # The failure is about the family track, never about the employee's group.
    assert "group" not in str(error.value)
    assert "at least 4 children under 23" in str(error.value)


def test_vehicle_above_group_rejected(synthetic_rules: RulesConfig) -> None:
    with pytest.raises(DomainValidationError, match="not available"):
        calculate_scenario(
            make_employee(), CarSelection.of(regular_car(group="ג")), synthetic_rules
        )


def test_comparison_net_difference(synthetic_rules: RulesConfig) -> None:
    employee = make_employee()
    comparison = compare_scenarios(
        employee, CarSelection.of(regular_car()), CarSelection.waiver(), synthetic_rules
    )
    assert comparison.net_difference == D("938")
    assert comparison.current.net_salary == D("1921.05")
    assert comparison.alternative.net_salary == D("2859.05")
    assert comparison.rules_version == "test-1"
    reverse = compare_scenarios(
        employee, CarSelection.waiver(), CarSelection.of(regular_car()), synthetic_rules
    )
    assert reverse.net_difference == D("-938")


def test_family_versus_regular_difference(synthetic_rules: RulesConfig) -> None:
    employee = make_employee(children_under_23=4)
    comparison = compare_scenarios(
        employee, CarSelection.of(regular_car()), CarSelection.of(family_car()), synthetic_rules
    )
    assert comparison.net_difference == D("533.05") - D("1921.05")


def electric_car(**overrides: object):  # noqa: ANN201
    return regular_car(drive=DriveType.ELECTRIC, default_participation=D(0), **overrides)


def test_electric_gross_up_in_top_bracket(synthetic_rules: RulesConfig) -> None:
    employee = make_employee()
    result = calculate_scenario(employee, CarSelection.of(electric_car()), synthetic_rules)
    # Marginal retention at taxable income 3400: 1 - 0.30 - 0.05 - 0.04 = 0.61
    assert abs(result.electric_gross_up - D(100) / D("0.61")) < TOLERANCE
    assert abs(result.net_salary - result.net_before_electric_benefit - D(100)) < TOLERANCE
    assert result.electric_net_bonus == D(100)


def test_electric_gross_up_crossing_a_bracket(synthetic_rules: RulesConfig) -> None:
    employee = make_employee(base="1900", credit_points="0", pension_rate="0", study_fund_rate="0")
    car = electric_car(monthly_use_value=D(0))
    result = calculate_scenario(employee, CarSelection.of(car), synthetic_rules)
    # 100 more taxable income at 0.71 retention reaches the 2000 limit, then 0.61.
    assert abs(result.electric_gross_up - (D(100) + D(29) / D("0.61"))) < TOLERANCE
    assert abs(result.net_salary - result.net_before_electric_benefit - D(100)) < TOLERANCE


def test_electric_gross_up_crossing_national_insurance_ceiling(
    synthetic_rules: RulesConfig,
) -> None:
    employee = make_employee(base="4950", credit_points="0", pension_rate="0", study_fund_rate="0")
    car = electric_car(monthly_use_value=D(0))
    result = calculate_scenario(employee, CarSelection.of(car), synthetic_rules)
    # 50 to the ceiling at 0.61, then no social charges: retention 0.70.
    assert abs(result.electric_gross_up - (D(50) + D("69.5") / D("0.70"))) < TOLERANCE
    assert abs(result.net_salary - result.net_before_electric_benefit - D(100)) < TOLERANCE


def test_electric_gross_up_in_zero_tax_region(synthetic_rules: RulesConfig) -> None:
    employee = make_employee(base="600", pension_rate="0", study_fund_rate="0")
    car = electric_car(monthly_use_value=D(0))
    result = calculate_scenario(employee, CarSelection.of(car), synthetic_rules)
    # Credits cover all tax here; only social charges (0.05 + 0.04) are retained.
    assert abs(result.electric_gross_up - D(100) / D("0.91")) < TOLERANCE
    assert result.income_tax == 0


@pytest.mark.parametrize("drive", [DriveType.PETROL, DriveType.HYBRID, DriveType.PLUG_IN])
def test_no_electric_benefit_for_non_electric(
    synthetic_rules: RulesConfig, drive: DriveType
) -> None:
    result = calculate_scenario(
        make_employee(), CarSelection.of(regular_car(drive=drive)), synthetic_rules
    )
    assert result.electric_gross_up == 0
    assert result.electric_net_bonus == 0
    assert result.net_salary == result.net_before_electric_benefit


def test_mock_rules_regular_and_waiver(mock_rules: RulesConfig) -> None:
    employee = make_employee(
        base="15000", credit_points="2.25", group="ב", waiver_maintenance=D(1500)
    )
    car = make_vehicle(group="ב", monthly_use_value=D(2690), default_participation=D(150))
    result = calculate_scenario(employee, CarSelection.of(car), mock_rules)
    assert result.tax_before_credits == D("2823.4")
    assert result.credit_points_credit == D("544.5")
    assert result.pension_credit == D("232.75")
    assert result.income_tax == D("2046.15")
    assert result.national_insurance == D("789.9888")
    assert result.health_insurance == D("768.6462")
    assert result.net_salary == D("9970.2150")
    waiver = calculate_scenario(employee, CarSelection.waiver(), mock_rules)
    assert waiver.net_salary == D("12133.938")
    assert waiver.rules_version == mock_rules.version


def test_decomposition_identity(mock_rules: RulesConfig) -> None:
    employee = make_employee(base="15000", credit_points="2.25", group="ב")
    car = make_vehicle(
        group="ב", drive=DriveType.ELECTRIC, monthly_use_value=D(2690), default_participation=D(150)
    )
    r = calculate_scenario(employee, CarSelection.of(car), mock_rules)
    rebuilt = (
        r.gross_salary
        + r.waiver_maintenance
        + r.electric_gross_up
        - r.income_tax
        - r.national_insurance
        - r.health_insurance
        - r.pension_contribution
        - r.study_fund_contribution
        - r.participation
    )
    assert abs(rebuilt - r.net_salary) < D("1e-20")  # test sums at default 28-digit precision
    assert abs(r.net_salary - r.net_before_electric_benefit - mock_rules.electric.net_bonus) < (
        TOLERANCE
    )


def test_deterministic(mock_rules: RulesConfig) -> None:
    employee = make_employee(base="15000", group="ב")
    car = make_vehicle(group="ב", drive=DriveType.ELECTRIC)
    first = calculate_scenario(employee, CarSelection.of(car), mock_rules)
    second = calculate_scenario(employee, CarSelection.of(car), mock_rules)
    assert first == second


def test_unsupported_rules_fail_closed(synthetic_rules: RulesConfig) -> None:
    from dataclasses import replace

    bad_method = replace(synthetic_rules.net_method, participation_reduces_value_of_use=True)
    bad_rules = replace(synthetic_rules, net_method=bad_method)
    with pytest.raises(UnsupportedRuleError, match="reducesValueOfUse"):
        calculate_scenario(make_employee(), CarSelection.of(regular_car()), bad_rules)


@pytest.mark.parametrize(
    ("amount", "expected"),
    [("1921.05", "1921"), ("0.5", "1"), ("1.4999", "1"), ("-0.5", "-1"), ("2.5", "3")],
)
def test_display_rounding(amount: str, expected: str) -> None:
    assert round_to_shekel(D(amount)) == D(expected)


def test_display_rounding_does_not_change_result(synthetic_rules: RulesConfig) -> None:
    result = calculate_scenario(make_employee(), CarSelection.of(regular_car()), synthetic_rules)
    assert result.net_salary == D("1921.05")
    assert round_to_shekel(result.net_salary) == D(1921)


@pytest.mark.parametrize(
    "build",
    [
        lambda: SalaryComponents(base=D(-1)),
        lambda: SalaryComponents(base=D(0)),
        lambda: SalaryComponents(base=D(1000), bonus=D(-5)),
        lambda: SalaryComponents(base=1000.0),  # type: ignore[arg-type]
        lambda: SalaryComponents(base=D("NaN")),
        lambda: make_employee(credit_points="-1"),
        lambda: make_employee(pension_rate="1.5"),
        lambda: make_employee(study_fund_rate="-0.1"),
        lambda: EmployeeProfile(  # type: ignore[arg-type]
            occupation=make_occupation(),
            salary=SalaryComponents(base=D(1000)),
            credit_points=D(0),
            pension_rate=0.06,
            study_fund_rate=D(0),
        ),
    ],
)
def test_invalid_inputs_rejected(build) -> None:  # noqa: ANN001
    with pytest.raises(DomainValidationError):
        build()


def test_zero_rates_and_credits_are_valid(synthetic_rules: RulesConfig) -> None:
    employee = make_employee(credit_points="0", pension_rate="0", study_fund_rate="0")
    result = calculate_scenario(employee, CarSelection.waiver(), synthetic_rules)
    assert result.pension_credit == 0
    assert result.net_salary > 0
