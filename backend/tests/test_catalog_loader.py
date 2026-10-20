from pathlib import Path

import pytest
from helpers import CATALOG_HEADER, MOCK_DIR, catalog_row, write_csv

from app.domain.models import DriveType, Vehicle, VehicleTrack
from app.domain.rules import RulesConfig
from app.ingestion.catalog_loader import load_vehicle_catalog
from app.ingestion.errors import DataValidationError


def test_mock_catalog_loads_20_vehicles(mock_vehicles: tuple[Vehicle, ...]) -> None:
    assert len(mock_vehicles) == 20
    assert [v.vehicle_id for v in mock_vehicles] == [f"CAR-{n:02d}" for n in range(1, 21)]


def test_codes_keep_leading_zeros_as_strings(mock_vehicles: tuple[Vehicle, ...]) -> None:
    kia_picanto = next(v for v in mock_vehicles if v.vehicle_id == "CAR-01")
    assert kia_picanto.manufacturer_code == "00885"
    assert all(len(v.manufacturer_code) == 5 and len(v.model_code) == 5 for v in mock_vehicles)
    assert any(v.model_code.startswith("0") for v in mock_vehicles)


def test_family_track_is_separate_from_regular_groups(mock_vehicles: tuple[Vehicle, ...]) -> None:
    family = [v for v in mock_vehicles if v.track is VehicleTrack.FAMILY]
    assert {v.vehicle_id for v in family} == {"CAR-19", "CAR-20"}
    assert all(v.group is None for v in family)
    regular = [v for v in mock_vehicles if v.track is VehicleTrack.REGULAR]
    assert len(regular) == 18
    assert {v.group for v in regular} == {"א", "ב", "ג", "ד"}


def test_electric_classification_uses_catalog_label(mock_vehicles: tuple[Vehicle, ...]) -> None:
    electric = {v.vehicle_id for v in mock_vehicles if v.is_electric}
    assert electric == {"CAR-03", "CAR-06", "CAR-08", "CAR-10", "CAR-11", "CAR-14", "CAR-17"}
    plug_in = next(v for v in mock_vehicles if v.drive is DriveType.PLUG_IN)
    assert not plug_in.is_electric


def test_unknown_group_is_rejected(tmp_path: Path, synthetic_rules: RulesConfig) -> None:
    path = write_csv(tmp_path / "c.csv", CATALOG_HEADER, [catalog_row("V-1", קבוצה="ה")])
    with pytest.raises(DataValidationError, match="unknown group 'ה'"):
        load_vehicle_catalog(path, synthetic_rules)


def test_family_vehicle_must_use_family_label(tmp_path: Path, synthetic_rules: RulesConfig) -> None:
    rows = [catalog_row("V-FAM", קבוצה="א")]
    path = write_csv(tmp_path / "c.csv", CATALOG_HEADER, rows)
    with pytest.raises(DataValidationError, match="family-track vehicle"):
        load_vehicle_catalog(path, synthetic_rules)


def test_family_vehicle_missing_from_catalog_is_rejected(
    tmp_path: Path, synthetic_rules: RulesConfig
) -> None:
    path = write_csv(tmp_path / "c.csv", CATALOG_HEADER, [catalog_row("V-1")])
    with pytest.raises(DataValidationError, match="missing from catalog"):
        load_vehicle_catalog(path, synthetic_rules)


def test_duplicate_id_is_rejected(tmp_path: Path, synthetic_rules: RulesConfig) -> None:
    rows = [catalog_row("V-1"), catalog_row("V-1", **{"תאור דגם": "OTHER"})]
    path = write_csv(tmp_path / "c.csv", CATALOG_HEADER, rows)
    with pytest.raises(DataValidationError, match="duplicate vehicle id 'V-1'"):
        load_vehicle_catalog(path, synthetic_rules)


def test_duplicate_key_is_rejected(tmp_path: Path, synthetic_rules: RulesConfig) -> None:
    rows = [catalog_row("V-1", **{"תאור דגם": "SAME"}), catalog_row("V-2", **{"תאור דגם": "SAME"})]
    path = write_csv(tmp_path / "c.csv", CATALOG_HEADER, rows)
    with pytest.raises(DataValidationError, match="duplicate vehicle key"):
        load_vehicle_catalog(path, synthetic_rules)


def test_missing_column_is_rejected(tmp_path: Path, synthetic_rules: RulesConfig) -> None:
    header = [column for column in CATALOG_HEADER if column != "קוד דגם"]
    path = write_csv(tmp_path / "c.csv", header, [[""] * len(header)])
    with pytest.raises(DataValidationError, match="missing columns"):
        load_vehicle_catalog(path, synthetic_rules)


def test_empty_cell_is_rejected_with_location(tmp_path: Path, synthetic_rules: RulesConfig) -> None:
    path = write_csv(tmp_path / "c.csv", CATALOG_HEADER, [catalog_row("V-1", **{"קוד דגם": ""})])
    with pytest.raises(DataValidationError, match=r"c\.csv line 2: empty value in column"):
        load_vehicle_catalog(path, synthetic_rules)


def test_non_numeric_price_is_rejected(tmp_path: Path, synthetic_rules: RulesConfig) -> None:
    path = write_csv(
        tmp_path / "c.csv", CATALOG_HEADER, [catalog_row("V-1", **{"מחיר מחירון": "abc"})]
    )
    with pytest.raises(DataValidationError, match="not a number"):
        load_vehicle_catalog(path, synthetic_rules)


def test_unknown_drive_type_is_rejected(tmp_path: Path, synthetic_rules: RulesConfig) -> None:
    path = write_csv(tmp_path / "c.csv", CATALOG_HEADER, [catalog_row("V-1", הנעה="דיזל")])
    with pytest.raises(DataValidationError, match="unknown drive type"):
        load_vehicle_catalog(path, synthetic_rules)


def test_ragged_row_is_rejected(tmp_path: Path, synthetic_rules: RulesConfig) -> None:
    path = write_csv(tmp_path / "c.csv", CATALOG_HEADER, [catalog_row("V-1")[:-1]])
    with pytest.raises(DataValidationError, match="expected 13 fields"):
        load_vehicle_catalog(path, synthetic_rules)


def test_non_utf8_file_is_rejected(tmp_path: Path, synthetic_rules: RulesConfig) -> None:
    path = tmp_path / "c.csv"
    path.write_bytes(b"\xff\xfe\x00bad")
    with pytest.raises(DataValidationError, match="not valid UTF-8"):
        load_vehicle_catalog(path, synthetic_rules)


def test_mock_catalog_file_is_readable_by_loader_directly(mock_rules: RulesConfig) -> None:
    assert len(load_vehicle_catalog(MOCK_DIR / "vehicle_catalog.csv", mock_rules)) == 20
