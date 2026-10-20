from decimal import Decimal

import pytest
from helpers import make_vehicle

from app.domain.eligibility import allowed_groups, can_choose_vehicle, is_family_track_eligible
from app.domain.errors import DomainValidationError
from app.domain.models import Vehicle, VehicleTrack
from app.domain.participation import employee_participation, family_track_gap_share
from app.domain.rules import RulesConfig


def test_four_children_under_23_are_required(mock_rules: RulesConfig) -> None:
    family = mock_rules.family_track
    assert not is_family_track_eligible(0, family)
    assert not is_family_track_eligible(3, family)
    assert is_family_track_eligible(4, family)
    assert is_family_track_eligible(5, family)


def test_age_limit_is_exclusive_in_rules(mock_rules: RulesConfig) -> None:
    # The caller counts only children below this age; a child who is 23 is not counted.
    assert mock_rules.family_track.child_age_limit == 23


def test_negative_children_count_is_rejected(mock_rules: RulesConfig) -> None:
    with pytest.raises(DomainValidationError, match="negative"):
        is_family_track_eligible(-1, mock_rules.family_track)


def test_eligibility_uses_configured_limits(synthetic_rules: RulesConfig) -> None:
    assert synthetic_rules.family_track.child_age_limit == 23
    assert synthetic_rules.family_track.min_children == 4


def test_family_gap_share_is_half_of_gap_against_group_budget() -> None:
    result = family_track_gap_share(Decimal(6000), Decimal(3500), Decimal("0.5"))
    assert result == Decimal(1250)


def test_family_gap_share_is_never_negative() -> None:
    assert family_track_gap_share(Decimal(3000), Decimal(3500), Decimal("0.5")) == Decimal(0)
    assert family_track_gap_share(Decimal(3500), Decimal(3500), Decimal("0.5")) == Decimal(0)


def test_family_vehicle_participation_adds_gap_share_to_default(
    mock_vehicles: tuple[Vehicle, ...], mock_rules: RulesConfig
) -> None:
    carnival = next(v for v in mock_vehicles if v.vehicle_id == "CAR-19")
    assert carnival.default_participation == Decimal(500)
    assert carnival.monthly_company_cost == Decimal(6000)
    # default 500 + 50% of (6000 - group budget)
    expected = {"א": 1750, "ב": 1650, "ג": 1250, "ד": 900}
    for group, amount in expected.items():
        assert employee_participation(carnival, group, mock_rules) == Decimal(amount)


def test_family_participation_follows_rules_not_hardcoded_values(
    synthetic_rules: RulesConfig,
) -> None:
    vehicle = make_vehicle(
        vehicle_id="V-FAM",
        track=VehicleTrack.FAMILY,
        group=None,
        monthly_company_cost=Decimal(1800),
        default_participation=Decimal(999),
    )
    # group א budget 1000: 999 + 0.5 * (1800 - 1000)
    assert employee_participation(vehicle, "א", synthetic_rules) == Decimal(1399)
    # group ב budget 2000 exceeds the cost: default only, no gap share
    assert employee_participation(vehicle, "ב", synthetic_rules) == Decimal(999)


def test_family_participation_equals_default_when_cost_equals_budget(
    synthetic_rules: RulesConfig,
) -> None:
    vehicle = make_vehicle(
        track=VehicleTrack.FAMILY,
        group=None,
        monthly_company_cost=Decimal(1000),
        default_participation=Decimal(120),
    )
    assert employee_participation(vehicle, "א", synthetic_rules) == Decimal(120)


def test_regular_vehicle_uses_catalog_default(synthetic_rules: RulesConfig) -> None:
    vehicle = make_vehicle(default_participation=Decimal(75))
    assert employee_participation(vehicle, "ב", synthetic_rules) == Decimal(75)


def test_family_participation_rejects_unknown_group(synthetic_rules: RulesConfig) -> None:
    vehicle = make_vehicle(track=VehicleTrack.FAMILY, group=None)
    with pytest.raises(DomainValidationError, match="Unknown employee group"):
        employee_participation(vehicle, "משפחתי", synthetic_rules)


def test_own_group_or_lower(mock_rules: RulesConfig) -> None:
    assert allowed_groups("א", mock_rules) == ("א",)
    assert allowed_groups("ג", mock_rules) == ("א", "ב", "ג")
    with pytest.raises(DomainValidationError):
        allowed_groups("משפחתי", mock_rules)


def test_regular_vehicle_choice_follows_group_order(
    mock_vehicles: tuple[Vehicle, ...], mock_rules: RulesConfig
) -> None:
    group_b_car = next(v for v in mock_vehicles if v.group == "ב")
    assert not can_choose_vehicle(group_b_car, "א", 0, mock_rules)
    assert can_choose_vehicle(group_b_car, "ב", 0, mock_rules)
    assert can_choose_vehicle(group_b_car, "ד", 0, mock_rules)


def test_family_vehicle_requires_family_eligibility_not_group(
    mock_vehicles: tuple[Vehicle, ...], mock_rules: RulesConfig
) -> None:
    carnival = next(v for v in mock_vehicles if v.vehicle_id == "CAR-19")
    assert can_choose_vehicle(carnival, "א", 4, mock_rules)
    assert can_choose_vehicle(carnival, "ד", 4, mock_rules)
    assert not can_choose_vehicle(carnival, "ד", 3, mock_rules)
