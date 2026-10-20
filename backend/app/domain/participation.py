from decimal import Decimal

from app.domain.errors import DomainValidationError
from app.domain.models import Vehicle, VehicleTrack
from app.domain.rules import RulesConfig


def family_track_gap_share(
    monthly_company_cost: Decimal, group_budget: Decimal, employee_share: Decimal
) -> Decimal:
    """Employee share of the gap between company cost and the employee's group budget."""
    gap = max(Decimal(0), monthly_company_cost - group_budget)
    return gap * employee_share


def employee_participation(vehicle: Vehicle, employee_group: str, rules: RulesConfig) -> Decimal:
    """Monthly employee participation. Does not check eligibility to choose the vehicle.

    A family-track vehicle adds the employee's share of the gap (against the employee's own
    regular group budget) to the vehicle's catalog default participation.
    """
    if vehicle.track is VehicleTrack.FAMILY:
        budget = rules.group_budgets.get(employee_group)
        if budget is None:
            raise DomainValidationError(f"Unknown employee group: {employee_group!r}")
        return vehicle.default_participation + family_track_gap_share(
            vehicle.monthly_company_cost, budget, rules.family_track.employee_gap_share
        )
    return vehicle.default_participation
