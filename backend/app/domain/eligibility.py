from app.domain.errors import DomainValidationError
from app.domain.models import Vehicle, VehicleTrack
from app.domain.rules import FamilyTrackRules, RulesConfig


def is_family_track_eligible(children_under_23: int, family_track: FamilyTrackRules) -> bool:
    """True when the employee has enough children below the age limit (a child at it is out).

    The caller supplies the number of children who have not yet reached the limit.
    """
    if children_under_23 < 0:
        raise DomainValidationError(f"Number of children cannot be negative: {children_under_23}")
    return children_under_23 >= family_track.min_children


def allowed_groups(employee_group: str, rules: RulesConfig) -> tuple[str, ...]:
    """Own group and every lower group (`own_group_or_lower`), in group order."""
    if employee_group not in rules.group_order:
        raise DomainValidationError(f"Unknown employee group: {employee_group!r}")
    position = rules.group_order.index(employee_group)
    return rules.group_order[: position + 1]


def can_choose_vehicle(
    vehicle: Vehicle,
    employee_group: str,
    children_under_23: int,
    rules: RulesConfig,
) -> bool:
    groups = allowed_groups(employee_group, rules)
    if vehicle.track is VehicleTrack.FAMILY:
        return is_family_track_eligible(children_under_23, rules.family_track)
    return vehicle.group in groups
