from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class TaxBracket:
    # None marks the open-ended top bracket.
    upper_limit: Decimal | None
    rate: Decimal


@dataclass(frozen=True, slots=True)
class SocialChargeParams:
    threshold: Decimal
    ceiling: Decimal
    low_rate: Decimal
    high_rate: Decimal


@dataclass(frozen=True, slots=True)
class PensionCreditParams:
    rate: Decimal
    max_contribution_rate: Decimal
    income_ceiling: Decimal


@dataclass(frozen=True, slots=True)
class NetMethodParams:
    tax_year: int
    credit_point_value: Decimal
    brackets: tuple[TaxBracket, ...]
    national_insurance: SocialChargeParams
    health: SocialChargeParams
    pension_credit: PensionCreditParams
    contributions_base: str
    participation_treatment: str
    participation_reduces_value_of_use: bool
    rounding_during: str
    rounding_display: str


@dataclass(frozen=True, slots=True)
class ElectricBenefit:
    net_bonus: Decimal
    method: str


@dataclass(frozen=True, slots=True)
class FamilyTrackRules:
    min_children: int
    # Exclusive: a child counts only while younger than this age (a 23-year-old does not count).
    child_age_limit: int
    car_ids: frozenset[str]
    employee_gap_share: Decimal


@dataclass(frozen=True, slots=True)
class WaiverRules:
    allowed_by: str
    maintenance_taxable: bool
    maintenance_pensionable: bool


@dataclass(frozen=True, slots=True)
class RulesConfig:
    version: str
    # Free-text provenance of the data set (for example, that it is illustrative mock data).
    source_note: str
    group_order: tuple[str, ...]
    group_budgets: Mapping[str, Decimal]
    choose_from: str
    electric: ElectricBenefit
    family_track: FamilyTrackRules
    waiver: WaiverRules
    unused_budget: str
    net_method: NetMethodParams
