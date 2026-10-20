import json
from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path
from typing import Any

from app.domain.rules import (
    ElectricBenefit,
    FamilyTrackRules,
    NetMethodParams,
    PensionCreditParams,
    RulesConfig,
    SocialChargeParams,
    TaxBracket,
    WaiverRules,
)
from app.ingestion.errors import DataValidationError

_SUPPORTED_CHOOSE_FROM = "own_group_or_lower"
_SUPPORTED_ELECTRIC_METHOD = "gross_up"


def load_rules(path: Path) -> RulesConfig:
    """Load and validate the rules file. Numbers are parsed as Decimal, never as float."""
    try:
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle, parse_float=Decimal)
    except FileNotFoundError:
        raise DataValidationError(f"{path.name}: file not found") from None
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise DataValidationError(f"{path.name}: not valid UTF-8 JSON ({error})") from None
    if not isinstance(data, dict):
        raise DataValidationError(f"{path.name}: top level must be an object")
    return _parse_rules(data, path.name)


def _parse_rules(data: Mapping[str, Any], name: str) -> RulesConfig:
    group_order = tuple(_text_list(data, "groupOrder", name))
    if not group_order or len(set(group_order)) != len(group_order):
        raise DataValidationError(f"{name}: groupOrder must be non-empty and unique")
    budgets_raw = _mapping(data, "budgets", name)
    if set(budgets_raw) != set(group_order):
        raise DataValidationError(f"{name}: budgets keys must equal groupOrder {list(group_order)}")
    budgets = {group: _decimal(budgets_raw, group, f"{name} budgets") for group in group_order}
    ordered = [budgets[group] for group in group_order]
    if any(budget <= 0 for budget in ordered) or any(
        later <= earlier for earlier, later in zip(ordered, ordered[1:], strict=False)
    ):
        raise DataValidationError(f"{name}: budgets must be positive and rise with groupOrder")

    choose_from = _text(data, "chooseFrom", name)
    if choose_from != _SUPPORTED_CHOOSE_FROM:
        raise DataValidationError(f"{name}: unsupported chooseFrom {choose_from!r}")

    return RulesConfig(
        version=_text(data, "version", name),
        source_note=_text(data, "note", name),
        group_order=group_order,
        group_budgets=budgets,
        choose_from=choose_from,
        electric=_parse_electric(_mapping(data, "electric", name), name),
        family_track=_parse_family(_mapping(data, "familyTrack", name), name),
        waiver=_parse_waiver(_mapping(data, "waiver", name), name),
        unused_budget=_text(data, "unusedBudget", name),
        net_method=_parse_net_method(_mapping(data, "netMethod", name), name),
    )


def _parse_electric(data: Mapping[str, Any], name: str) -> ElectricBenefit:
    where = f"{name} electric"
    method = _text(data, "method", where)
    if method != _SUPPORTED_ELECTRIC_METHOD:
        raise DataValidationError(f"{where}: unsupported method {method!r}")
    bonus = _decimal(data, "netBonus", where)
    if bonus < 0:
        raise DataValidationError(f"{where}: netBonus cannot be negative")
    return ElectricBenefit(net_bonus=bonus, method=method)


def _parse_family(data: Mapping[str, Any], name: str) -> FamilyTrackRules:
    where = f"{name} familyTrack"
    car_ids = _text_list(data, "cars", where)
    if not car_ids or len(set(car_ids)) != len(car_ids):
        raise DataValidationError(f"{where}: cars must be non-empty and unique")
    share = _decimal(data, "gapSplitEmployee", where)
    if not Decimal(0) <= share <= Decimal(1):
        raise DataValidationError(f"{where}: gapSplitEmployee must be between 0 and 1")
    min_children = _int(data, "minChildren", where)
    age_limit = _int(data, "childMaxAge", where)
    if min_children < 1 or age_limit < 1:
        raise DataValidationError(f"{where}: minChildren and childMaxAge must be positive")
    return FamilyTrackRules(
        min_children=min_children,
        child_age_limit=age_limit,
        car_ids=frozenset(car_ids),
        employee_gap_share=share,
    )


def _parse_waiver(data: Mapping[str, Any], name: str) -> WaiverRules:
    where = f"{name} waiver"
    return WaiverRules(
        allowed_by=_text(data, "allowedBy", where),
        maintenance_taxable=_bool(data, "maintenanceIsTaxable", where),
        maintenance_pensionable=_bool(data, "maintenanceIsPensionable", where),
    )


def _parse_net_method(data: Mapping[str, Any], name: str) -> NetMethodParams:
    where = f"{name} netMethod"
    participation = _mapping(data, "participation", where)
    rounding = _mapping(data, "rounding", where)
    return NetMethodParams(
        tax_year=_int(data, "taxYear", where),
        credit_point_value=_decimal(data, "creditPointValue", where),
        brackets=_parse_brackets(data, where),
        national_insurance=_parse_social(_mapping(data, "nationalInsurance", where), where),
        health=_parse_social(_mapping(data, "health", where), where),
        pension_credit=_parse_pension(_mapping(data, "pensionCredit", where), where),
        contributions_base=_text(data, "contributionsBase", where),
        participation_treatment=_text(participation, "treatment", where),
        participation_reduces_value_of_use=_bool(participation, "reducesValueOfUse", where),
        rounding_during=_text(rounding, "during", where),
        rounding_display=_text(rounding, "display", where),
    )


def _parse_brackets(data: Mapping[str, Any], where: str) -> tuple[TaxBracket, ...]:
    raw = _require(data, "brackets", where)
    if not isinstance(raw, list) or not raw:
        raise DataValidationError(f"{where}: brackets must be a non-empty list")
    brackets: list[TaxBracket] = []
    for item in raw:
        if not isinstance(item, list) or len(item) != 2:
            raise DataValidationError(f"{where}: each bracket must be [upper_limit, rate]")
        limit, rate = item
        upper = None if limit is None else _as_decimal(limit, f"{where} bracket limit")
        brackets.append(TaxBracket(upper_limit=upper, rate=_rate(rate, f"{where} bracket rate")))
    limits = [bracket.upper_limit for bracket in brackets]
    finite = [limit for limit in limits[:-1] if limit is not None]
    if limits[-1] is not None or len(finite) != len(limits) - 1:
        raise DataValidationError(f"{where}: only the last bracket may be open-ended")
    if any(later <= earlier for earlier, later in zip(finite, finite[1:], strict=False)):
        raise DataValidationError(f"{where}: bracket limits must be strictly increasing")
    return tuple(brackets)


def _parse_social(data: Mapping[str, Any], where: str) -> SocialChargeParams:
    params = SocialChargeParams(
        threshold=_decimal(data, "threshold", where),
        ceiling=_decimal(data, "ceiling", where),
        low_rate=_rate(_require(data, "lowRate", where), f"{where} lowRate"),
        high_rate=_rate(_require(data, "highRate", where), f"{where} highRate"),
    )
    if params.ceiling <= params.threshold:
        raise DataValidationError(f"{where}: ceiling must be above threshold")
    return params


def _parse_pension(data: Mapping[str, Any], where: str) -> PensionCreditParams:
    return PensionCreditParams(
        rate=_rate(_require(data, "rate", where), f"{where} pension rate"),
        max_contribution_rate=_rate(
            _require(data, "maxContributionRate", where), f"{where} maxContributionRate"
        ),
        income_ceiling=_decimal(data, "incomeCeiling", where),
    )


def _require(data: Mapping[str, Any], key: str, where: str) -> Any:
    if key not in data:
        raise DataValidationError(f"{where}: missing field {key!r}")
    return data[key]


def _mapping(data: Mapping[str, Any], key: str, where: str) -> Mapping[str, Any]:
    value = _require(data, key, where)
    if not isinstance(value, dict):
        raise DataValidationError(f"{where}: field {key!r} must be an object")
    return value


def _text(data: Mapping[str, Any], key: str, where: str) -> str:
    value = _require(data, key, where)
    if not isinstance(value, str) or not value.strip():
        raise DataValidationError(f"{where}: field {key!r} must be a non-empty string")
    return value


def _text_list(data: Mapping[str, Any], key: str, where: str) -> list[str]:
    value = _require(data, key, where)
    if not isinstance(value, list) or not all(isinstance(v, str) and v for v in value):
        raise DataValidationError(f"{where}: field {key!r} must be a list of non-empty strings")
    return list(value)


def _bool(data: Mapping[str, Any], key: str, where: str) -> bool:
    value = _require(data, key, where)
    if not isinstance(value, bool):
        raise DataValidationError(f"{where}: field {key!r} must be true or false")
    return value


def _int(data: Mapping[str, Any], key: str, where: str) -> int:
    value = _require(data, key, where)
    if isinstance(value, bool) or not isinstance(value, int):
        raise DataValidationError(f"{where}: field {key!r} must be a whole number")
    return value


def _as_decimal(value: object, where: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, int | Decimal):
        raise DataValidationError(f"{where}: expected a number, got {value!r}")
    return Decimal(value)


def _decimal(data: Mapping[str, Any], key: str, where: str) -> Decimal:
    return _as_decimal(_require(data, key, where), f"{where} field {key!r}")


def _rate(value: object, where: str) -> Decimal:
    rate = _as_decimal(value, where)
    if not Decimal(0) <= rate <= Decimal(1):
        raise DataValidationError(f"{where}: rate must be between 0 and 1")
    return rate
