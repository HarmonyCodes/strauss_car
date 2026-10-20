from dataclasses import dataclass
from decimal import Decimal

from app.application.errors import UnknownReferenceError
from app.application.reference_data import ReferenceData
from app.domain.net_salary import compare_scenarios
from app.domain.scenario import CarSelection, ComparisonResult, EmployeeProfile, SalaryComponents


@dataclass(frozen=True, slots=True)
class CarChoice:
    """A catalog vehicle id, or None to waive the car."""

    vehicle_id: str | None


@dataclass(frozen=True, slots=True)
class ComparisonInput:
    occupation_name: str
    base_salary: Decimal
    commissions: Decimal
    bonus: Decimal
    credit_points: Decimal
    pension_rate: Decimal
    study_fund_rate: Decimal
    children_under_23: int
    current: CarChoice
    alternative: CarChoice


class ComparisonService:
    """Resolves ids against trusted reference data and delegates all maths to the domain."""

    def __init__(self, data: ReferenceData) -> None:
        self._data = data

    @property
    def data(self) -> ReferenceData:
        return self._data

    def compare(self, request: ComparisonInput) -> ComparisonResult:
        occupation = self._data.occupation(request.occupation_name)
        if occupation is None:
            raise UnknownReferenceError(f"Unknown occupation: {request.occupation_name!r}")
        employee = EmployeeProfile(
            occupation=occupation,
            salary=SalaryComponents(
                base=request.base_salary, commissions=request.commissions, bonus=request.bonus
            ),
            credit_points=request.credit_points,
            pension_rate=request.pension_rate,
            study_fund_rate=request.study_fund_rate,
            children_under_23=request.children_under_23,
        )
        return compare_scenarios(
            employee,
            self._selection(request.current),
            self._selection(request.alternative),
            self._data.rules,
        )

    def _selection(self, choice: CarChoice) -> CarSelection:
        if choice.vehicle_id is None:
            return CarSelection.waiver()
        vehicle = self._data.vehicle(choice.vehicle_id)
        if vehicle is None:
            raise UnknownReferenceError(f"Unknown vehicle id: {choice.vehicle_id!r}")
        return CarSelection.of(vehicle)
