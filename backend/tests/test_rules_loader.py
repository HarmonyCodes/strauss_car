from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from helpers import MOCK_DIR, synthetic_rules_dict, write_json

from app.domain.rules import RulesConfig
from app.ingestion.errors import DataValidationError
from app.ingestion.rules_loader import load_rules


def test_mock_rules_load_with_decimal_values(mock_rules: RulesConfig) -> None:
    assert mock_rules.version == "mock-2026-10-12"
    assert mock_rules.group_order == ("א", "ב", "ג", "ד")
    assert mock_rules.group_budgets["ד"] == Decimal(5200)
    assert mock_rules.electric.net_bonus == Decimal(250)
    assert mock_rules.family_track.car_ids == {"CAR-19", "CAR-20"}
    assert mock_rules.family_track.employee_gap_share == Decimal("0.5")
    assert mock_rules.family_track.child_age_limit == 23
    assert mock_rules.net_method.national_insurance.low_rate == Decimal("0.0104")
    assert mock_rules.net_method.brackets[-1].upper_limit is None
    assert mock_rules.waiver.maintenance_pensionable is False


def test_missing_file_is_reported() -> None:
    with pytest.raises(DataValidationError, match="file not found"):
        load_rules(MOCK_DIR / "does-not-exist.json")


def test_invalid_json_is_reported(tmp_path: Path) -> None:
    path = tmp_path / "rules.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(DataValidationError, match="not valid"):
        load_rules(path)


def _load_modified(tmp_path: Path, mutate: Any) -> RulesConfig:
    data = synthetic_rules_dict()
    mutate(data)
    return load_rules(write_json(tmp_path / "rules.json", data))


def test_missing_field_is_reported(tmp_path: Path) -> None:
    with pytest.raises(DataValidationError, match="missing field 'budgets'"):
        _load_modified(tmp_path, lambda d: d.pop("budgets"))


def test_budgets_must_match_group_order(tmp_path: Path) -> None:
    with pytest.raises(DataValidationError, match="budgets keys must equal groupOrder"):
        _load_modified(tmp_path, lambda d: d["budgets"].pop("ג"))


def test_budgets_must_rise_with_group_order(tmp_path: Path) -> None:
    with pytest.raises(DataValidationError, match="rise with groupOrder"):
        _load_modified(tmp_path, lambda d: d["budgets"].update({"ב": 500}))


def test_unsupported_choose_from_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(DataValidationError, match="unsupported chooseFrom"):
        _load_modified(tmp_path, lambda d: d.update({"chooseFrom": "any_group"}))


def test_unsupported_electric_method_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(DataValidationError, match="unsupported method"):
        _load_modified(tmp_path, lambda d: d["electric"].update({"method": "gross"}))


def test_gap_share_out_of_range_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(DataValidationError, match="gapSplitEmployee"):
        _load_modified(tmp_path, lambda d: d["familyTrack"].update({"gapSplitEmployee": 1.5}))


def test_last_bracket_must_be_open_ended(tmp_path: Path) -> None:
    with pytest.raises(DataValidationError, match="only the last bracket"):
        _load_modified(tmp_path, lambda d: d["netMethod"]["brackets"].append([5000, 0.4]))
