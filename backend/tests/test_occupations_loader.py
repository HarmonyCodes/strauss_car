from decimal import Decimal
from pathlib import Path

import pytest
from helpers import OCCUPATION_HEADER, occupation_row, write_csv

from app.domain.models import Occupation
from app.domain.rules import RulesConfig
from app.ingestion.errors import DataValidationError
from app.ingestion.occupations_loader import load_occupations


def test_mock_occupations_load_14(
    mock_occupations: tuple[Occupation, ...], mock_rules: RulesConfig
) -> None:
    assert len(mock_occupations) == 14
    assert all(o.group in mock_rules.group_order for o in mock_occupations)
    assert len({o.name for o in mock_occupations}) == 14


def test_mock_waiver_rules_are_consistent(mock_occupations: tuple[Occupation, ...]) -> None:
    for occupation in mock_occupations:
        assert occupation.car_mandatory != occupation.can_waive
        if occupation.can_waive:
            assert occupation.waiver_maintenance > 0
        else:
            assert occupation.waiver_maintenance == Decimal(0)
    assert {o.waiver_maintenance for o in mock_occupations if o.can_waive} == {
        Decimal(amount) for amount in (1200, 1500, 2000, 2600, 3000)
    }


def test_unknown_group_is_rejected(tmp_path: Path, synthetic_rules: RulesConfig) -> None:
    path = write_csv(
        tmp_path / "o.csv", OCCUPATION_HEADER, [occupation_row(**{"קבוצת זכאות": "ז"})]
    )
    with pytest.raises(DataValidationError, match="unknown eligibility group 'ז'"):
        load_occupations(path, synthetic_rules)


def test_family_label_is_not_an_eligibility_group(
    tmp_path: Path, synthetic_rules: RulesConfig
) -> None:
    path = write_csv(
        tmp_path / "o.csv", OCCUPATION_HEADER, [occupation_row(**{"קבוצת זכאות": "משפחתי"})]
    )
    with pytest.raises(DataValidationError, match="unknown eligibility group"):
        load_occupations(path, synthetic_rules)


def test_mandatory_car_and_waiver_together_is_rejected(
    tmp_path: Path, synthetic_rules: RulesConfig
) -> None:
    path = write_csv(tmp_path / "o.csv", OCCUPATION_HEADER, [occupation_row(**{"רכב חובה": "כן"})])
    with pytest.raises(DataValidationError, match="exactly one of"):
        load_occupations(path, synthetic_rules)


def test_maintenance_without_waiver_is_rejected(
    tmp_path: Path, synthetic_rules: RulesConfig
) -> None:
    row = occupation_row(**{"רכב חובה": "כן", "מותר לוותר": "לא", "אחזקת רכב בוויתור (₪)": "50"})
    path = write_csv(tmp_path / "o.csv", OCCUPATION_HEADER, [row])
    with pytest.raises(DataValidationError, match="cannot waive but has waiver maintenance"):
        load_occupations(path, synthetic_rules)


def test_invalid_yes_no_is_rejected(tmp_path: Path, synthetic_rules: RulesConfig) -> None:
    path = write_csv(
        tmp_path / "o.csv", OCCUPATION_HEADER, [occupation_row(**{"מותר לוותר": "אולי"})]
    )
    with pytest.raises(DataValidationError, match="must be 'כן' or 'לא'"):
        load_occupations(path, synthetic_rules)


def test_duplicate_occupation_is_rejected(tmp_path: Path, synthetic_rules: RulesConfig) -> None:
    path = write_csv(
        tmp_path / "o.csv", OCCUPATION_HEADER, [occupation_row("x"), occupation_row("x")]
    )
    with pytest.raises(DataValidationError, match="duplicate occupations"):
        load_occupations(path, synthetic_rules)


def test_empty_cell_and_missing_column_are_rejected(
    tmp_path: Path, synthetic_rules: RulesConfig
) -> None:
    empty = write_csv(tmp_path / "e.csv", OCCUPATION_HEADER, [occupation_row("")])
    with pytest.raises(DataValidationError, match="empty value in column 'עיסוק'"):
        load_occupations(empty, synthetic_rules)
    header = OCCUPATION_HEADER[:-1]
    missing = write_csv(tmp_path / "m.csv", header, [occupation_row()[:-1]])
    with pytest.raises(DataValidationError, match="missing columns"):
        load_occupations(missing, synthetic_rules)
