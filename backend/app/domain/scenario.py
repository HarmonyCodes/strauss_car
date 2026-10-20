from dataclasses import dataclass
from decimal import Decimal
from typing import Self

from app.domain.errors import DomainValidationError
from app.domain.models import Occupation, Vehicle
from app.domain.validation import require_decimal

_ZERO = Decimal(0)
_ONE = Decimal(1)


@dataclass(frozen=True, slots=True)
class SalaryComponents:
    """Monthly gross pay components. Pension and study fund are computed on their total."""

    base: Decimal
    commissions: Decimal = _ZERO
    bonus: Decimal = _ZERO

    def __post_init__(self) -> None:
        require_decimal("base salary", self.base)
        require_decimal("commissions", self.commissions)
        require_decimal("bonus", self.bonus)
        if self.total <= _ZERO:
            raise DomainValidationError("Gross salary must be positive")

    @property
    def total(self) -> Decimal:
        return self.base + self.commissions + self.bonus


@dataclass(frozen=True, slots=True)
class EmployeeProfile:
    """Synthetic or approved employee inputs needed for a net-salary scenario."""

    occupation: Occupation
    salary: SalaryComponents
    credit_points: Decimal
    pension_rate: Decimal
    study_fund_rate: Decimal
    children_under_23: int = 0

    def __post_init__(self) -> None:
        require_decimal("credit points", self.credit_points)
        require_decimal("pension rate", self.pension_rate, maximum=_ONE)
        require_decimal("study fund rate", self.study_fund_rate, maximum=_ONE)
        if isinstance(self.children_under_23, bool) or not isinstance(self.children_under_23, int):
            raise DomainValidationError("children_under_23 must be a whole number")
        if self.children_under_23 < 0:
            raise DomainValidationError("children_under_23 cannot be negative")

    @property
    def group(self) -> str:
        return self.occupation.group


@dataclass(frozen=True, slots=True)
class CarSelection:
    """A catalog vehicle, or None when the employee waives the car."""

    vehicle: Vehicle | None

    @classmethod
    def of(cls, vehicle: Vehicle) -> Self:
        return cls(vehicle=vehicle)

    @classmethod
    def waiver(cls) -> Self:
        return cls(vehicle=None)

    @property
    def is_waiver(self) -> bool:
        return self.vehicle is None


@dataclass(frozen=True, slots=True)
class ScenarioResult:
    """Unrounded monthly breakdown of one scenario. All amounts are Decimal shekels."""

    rules_version: str
    rules_source_note: str
    tax_table_year: int
    vehicle_id: str | None
    is_waiver: bool
    # Pay and benefits
    gross_salary: Decimal
    use_value: Decimal
    waiver_maintenance: Decimal
    electric_gross_up: Decimal
    electric_net_bonus: Decimal
    # Tax computation
    taxable_income: Decimal
    tax_before_credits: Decimal
    credit_points_credit: Decimal
    pension_credit: Decimal
    income_tax: Decimal
    # Other deductions
    national_insurance: Decimal
    health_insurance: Decimal
    pension_contribution: Decimal
    study_fund_contribution: Decimal
    participation: Decimal
    # Result
    net_before_electric_benefit: Decimal
    net_salary: Decimal
    assumptions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ComparisonResult:
    current: ScenarioResult
    alternative: ScenarioResult
    # Alternative net minus current net; positive means the alternative leaves more net pay.
    net_difference: Decimal
    rules_version: str
