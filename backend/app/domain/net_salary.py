from dataclasses import dataclass
from decimal import Decimal, localcontext

from app.domain.eligibility import can_choose_vehicle, is_family_track_eligible
from app.domain.errors import DomainValidationError, UnsupportedRuleError
from app.domain.gross_up import solve_gross_up
from app.domain.models import VehicleTrack
from app.domain.participation import employee_participation
from app.domain.rules import NetMethodParams, RulesConfig
from app.domain.scenario import CarSelection, ComparisonResult, EmployeeProfile, ScenarioResult
from app.domain.tax import (
    income_tax_before_credits,
    pension_credit,
    social_charge,
    taxable_income_for_tax,
)

_ZERO = Decimal(0)
# Enough digits that the only division (the electric gross-up) stays exact for practical purposes.
_PRECISION = 60

CALCULATION_ASSUMPTIONS = (
    "ILLUSTRATIVE_PARAMETERS: tax, social-charge and credit parameters come from the rules file "
    "and are illustrative; results are not payroll or tax advice.",
    "HEALTH_BASE: the health-insurance base is treated like the national-insurance base "
    "(includes value of use, taxable maintenance and the electric gross-up); the rules state this "
    "only for income tax and national insurance.",
    "TAXABLE_ADDONS: taxable add-ons (value of use, taxable waiver maintenance, electric "
    "gross-up) enter the income-tax, national-insurance and health bases.",
    "ELECTRIC_NOT_PENSIONABLE: the electric benefit is not part of the pension and study-fund "
    "base; the rules define that base as base salary, commissions and bonus.",
    "PENSION_CREDIT_INCOME: the pension-credit qualifying income is the pensionable gross, "
    "capped at the configured income ceiling.",
    "CONTRIBUTIONS_NET_DEDUCTION: employee pension and study-fund contributions are deducted "
    "from net pay; only the pension credit reduces tax.",
    "CREDITS_NOT_REFUNDABLE: credits cannot reduce income tax below zero.",
)


@dataclass(frozen=True, slots=True)
class _Fixed:
    """Amounts that do not depend on the electric gross-up."""

    gross: Decimal
    use_value: Decimal
    taxable_maintenance: Decimal
    untaxed_maintenance: Decimal
    participation: Decimal
    pension_contribution: Decimal
    study_fund_contribution: Decimal
    credit_points_credit: Decimal
    pension_credit: Decimal

    @property
    def base_taxable_income(self) -> Decimal:
        return self.gross + self.use_value + self.taxable_maintenance

    @property
    def credits_total(self) -> Decimal:
        return self.credit_points_credit + self.pension_credit


@dataclass(frozen=True, slots=True)
class _Evaluation:
    taxable_income: Decimal
    tax_before_credits: Decimal
    income_tax: Decimal
    national_insurance: Decimal
    health_insurance: Decimal
    net: Decimal


def calculate_scenario(
    employee: EmployeeProfile, selection: CarSelection, rules: RulesConfig
) -> ScenarioResult:
    """Monthly net salary for one car scenario, computed deterministically without rounding."""
    _ensure_supported(rules)
    _validate_selection(employee, selection, rules)
    params = rules.net_method
    vehicle = selection.vehicle
    with localcontext() as context:
        context.prec = _PRECISION
        maintenance = employee.occupation.waiver_maintenance if vehicle is None else _ZERO
        taxable_maintenance = maintenance if rules.waiver.maintenance_taxable else _ZERO
        pension_base = employee.salary.total
        if rules.waiver.maintenance_pensionable:
            pension_base += maintenance
        pension_contribution = employee.pension_rate * pension_base
        fixed = _Fixed(
            gross=employee.salary.total,
            use_value=vehicle.monthly_use_value if vehicle is not None else _ZERO,
            taxable_maintenance=taxable_maintenance,
            untaxed_maintenance=maintenance - taxable_maintenance,
            participation=(
                employee_participation(vehicle, employee.group, rules)
                if vehicle is not None
                else _ZERO
            ),
            pension_contribution=pension_contribution,
            study_fund_contribution=employee.study_fund_rate * pension_base,
            credit_points_credit=employee.credit_points * params.credit_point_value,
            pension_credit=pension_credit(
                pension_base, pension_contribution, params.pension_credit
            ),
        )
        without_benefit = _evaluate(fixed, params, _ZERO)
        gross_up = _ZERO
        net_bonus = _ZERO
        if vehicle is not None and vehicle.is_electric:
            net_bonus = rules.electric.net_bonus
            gross_up = solve_gross_up(
                net_bonus,
                lambda amount: _evaluate(fixed, params, amount).net,
                _gross_up_breakpoints(fixed, params),
            )
        final = _evaluate(fixed, params, gross_up)
    return ScenarioResult(
        rules_version=rules.version,
        rules_source_note=rules.source_note,
        tax_table_year=params.tax_year,
        vehicle_id=vehicle.vehicle_id if vehicle is not None else None,
        is_waiver=vehicle is None,
        gross_salary=fixed.gross,
        use_value=fixed.use_value,
        waiver_maintenance=maintenance,
        electric_gross_up=gross_up,
        electric_net_bonus=net_bonus,
        taxable_income=final.taxable_income,
        tax_before_credits=final.tax_before_credits,
        credit_points_credit=fixed.credit_points_credit,
        pension_credit=fixed.pension_credit,
        income_tax=final.income_tax,
        national_insurance=final.national_insurance,
        health_insurance=final.health_insurance,
        pension_contribution=fixed.pension_contribution,
        study_fund_contribution=fixed.study_fund_contribution,
        participation=fixed.participation,
        net_before_electric_benefit=without_benefit.net,
        net_salary=final.net,
        assumptions=CALCULATION_ASSUMPTIONS,
    )


def compare_scenarios(
    employee: EmployeeProfile,
    current: CarSelection,
    alternative: CarSelection,
    rules: RulesConfig,
) -> ComparisonResult:
    current_result = calculate_scenario(employee, current, rules)
    alternative_result = calculate_scenario(employee, alternative, rules)
    return ComparisonResult(
        current=current_result,
        alternative=alternative_result,
        net_difference=alternative_result.net_salary - current_result.net_salary,
        rules_version=rules.version,
    )


def _evaluate(fixed: _Fixed, params: NetMethodParams, gross_up: Decimal) -> _Evaluation:
    taxable_income = fixed.base_taxable_income + gross_up
    tax_before_credits = income_tax_before_credits(taxable_income, params.brackets)
    income_tax = max(_ZERO, tax_before_credits - fixed.credits_total)
    national_insurance = social_charge(taxable_income, params.national_insurance)
    health_insurance = social_charge(taxable_income, params.health)
    cash = fixed.gross + fixed.taxable_maintenance + fixed.untaxed_maintenance + gross_up
    net = (
        cash
        - income_tax
        - national_insurance
        - health_insurance
        - fixed.pension_contribution
        - fixed.study_fund_contribution
        - fixed.participation
    )
    return _Evaluation(
        taxable_income=taxable_income,
        tax_before_credits=tax_before_credits,
        income_tax=income_tax,
        national_insurance=national_insurance,
        health_insurance=health_insurance,
        net=net,
    )


def _gross_up_breakpoints(fixed: _Fixed, params: NetMethodParams) -> list[Decimal]:
    """Gross-up amounts where net pay changes slope (bracket, social-charge and credit kinks)."""
    incomes = [b.upper_limit for b in params.brackets if b.upper_limit is not None]
    for charge in (params.national_insurance, params.health):
        incomes.extend((charge.threshold, charge.ceiling))
    zero_tax_income = taxable_income_for_tax(params.brackets, fixed.credits_total)
    if zero_tax_income is not None:
        incomes.append(zero_tax_income)
    return [income - fixed.base_taxable_income for income in incomes]


def _ensure_supported(rules: RulesConfig) -> None:
    method = rules.net_method
    unsupported: list[str] = []
    if method.contributions_base != "gross":
        unsupported.append(f"contributionsBase={method.contributions_base!r}")
    if method.participation_treatment != "net_deduction":
        unsupported.append(f"participation.treatment={method.participation_treatment!r}")
    if method.participation_reduces_value_of_use:
        unsupported.append("participation.reducesValueOfUse=true")
    if method.rounding_during != "none":
        unsupported.append(f"rounding.during={method.rounding_during!r}")
    if rules.electric.method != "gross_up":
        unsupported.append(f"electric.method={rules.electric.method!r}")
    if rules.waiver.allowed_by != "occupation":
        unsupported.append(f"waiver.allowedBy={rules.waiver.allowed_by!r}")
    if rules.unused_budget != "not_paid":
        unsupported.append(f"unusedBudget={rules.unused_budget!r}")
    if unsupported:
        raise UnsupportedRuleError(f"Unsupported rules: {', '.join(unsupported)}")


def _validate_selection(
    employee: EmployeeProfile, selection: CarSelection, rules: RulesConfig
) -> None:
    occupation = employee.occupation
    vehicle = selection.vehicle
    if vehicle is None:
        if not occupation.can_waive:
            raise DomainValidationError(f"Occupation {occupation.name!r} may not waive the car")
        return
    if vehicle.track is VehicleTrack.FAMILY:
        if not is_family_track_eligible(employee.children_under_23, rules.family_track):
            raise DomainValidationError(
                f"Family-track eligibility conditions are not met for {vehicle.vehicle_id}: "
                f"at least {rules.family_track.min_children} children under "
                f"{rules.family_track.child_age_limit} are required"
            )
        return
    if not can_choose_vehicle(vehicle, employee.group, employee.children_under_23, rules):
        raise DomainValidationError(
            f"Vehicle {vehicle.vehicle_id} is not available to group {employee.group!r} "
            "with the given children"
        )
