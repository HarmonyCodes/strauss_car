from decimal import Decimal
from pathlib import Path

import pytest
from helpers import MOCK_DIR, USE_VALUE_HEADER, make_vehicle, write_csv

from app.domain.errors import AmbiguousVehicleMatchError, NoVehicleMatchError
from app.domain.models import Vehicle
from app.domain.use_value import UseValueIndex, UseValueRecord, mismatched_fields
from app.ingestion.errors import DataValidationError
from app.ingestion.use_value_loader import load_use_value_records

# Tax year of the reference file ("הקובץ המורחב 2026" in the rules source).
TAX_YEAR = 2026


def _record(**overrides: object) -> UseValueRecord:
    fields: dict[str, object] = {
        "tax_year": TAX_YEAR,
        "registration_year": 2025,
        "vehicle_type_code": "1",
        "manufacturer_code": "00123",
        "model_code": "00045",
        "model_description": "DESC",
        "list_price": Decimal(100000),
        "monthly_use_value": Decimal(2000),
    }
    fields.update(overrides)
    return UseValueRecord(**fields)  # type: ignore[arg-type]


def test_lookup_returns_the_single_match() -> None:
    index = UseValueIndex([_record()])
    assert index.find_for_vehicle(make_vehicle(), TAX_YEAR).monthly_use_value == Decimal(2000)


def test_description_disambiguates_records_sharing_other_codes() -> None:
    index = UseValueIndex(
        [
            _record(vehicle_type_code="1", model_description="DESC"),
            _record(vehicle_type_code="2", model_description="OTHER", monthly_use_value=Decimal(9)),
        ]
    )
    assert index.find_for_vehicle(make_vehicle(), TAX_YEAR).vehicle_type_code == "1"


def test_ambiguous_match_is_reported_not_guessed() -> None:
    index = UseValueIndex([_record(vehicle_type_code="1"), _record(vehicle_type_code="2")])
    with pytest.raises(AmbiguousVehicleMatchError, match="2 use-value records"):
        index.find_for_vehicle(make_vehicle(), TAX_YEAR)


def test_missing_match_is_reported() -> None:
    index = UseValueIndex([_record(model_code="99999")])
    with pytest.raises(NoVehicleMatchError):
        index.find_for_vehicle(make_vehicle(), TAX_YEAR)


@pytest.mark.parametrize(
    "override",
    [
        {"registration_year": 2024},
        {"tax_year": 2025},
        {"manufacturer_code": "00124"},
        {"model_code": "00046"},
    ],
)
def test_every_key_part_must_match(override: dict[str, int | str]) -> None:
    index = UseValueIndex([_record(**override)])
    with pytest.raises(NoVehicleMatchError):
        index.find_for_vehicle(make_vehicle(), TAX_YEAR)


def test_optional_vehicle_type_code_narrows_the_match() -> None:
    index = UseValueIndex([_record(vehicle_type_code="1"), _record(vehicle_type_code="2")])
    found = index.find(
        tax_year=TAX_YEAR,
        registration_year=2025,
        manufacturer_code="00123",
        model_code="00045",
        model_description="DESC",
        vehicle_type_code="2",
    )
    assert found.vehicle_type_code == "2"


def test_mismatched_fields_reports_price_and_use_value() -> None:
    vehicle = make_vehicle()
    assert mismatched_fields(vehicle, _record()) == ()
    different = _record(list_price=Decimal(1), monthly_use_value=Decimal(2))
    assert mismatched_fields(vehicle, different) == ("list_price", "monthly_use_value")


def test_loader_keeps_codes_as_strings_and_rejects_duplicate_keys(tmp_path: Path) -> None:
    row = ["2026", "2025", "1", "00123", "00045", "DESC", "100000", "2000"]
    records = load_use_value_records(write_csv(tmp_path / "t.csv", USE_VALUE_HEADER, [row]))
    assert records[0].manufacturer_code == "00123"
    assert records[0].model_code == "00045"
    duplicate = write_csv(tmp_path / "d.csv", USE_VALUE_HEADER, [row, row])
    with pytest.raises(DataValidationError, match="duplicate use-value key"):
        load_use_value_records(duplicate)


def test_loader_rejects_missing_column_and_empty_cell(tmp_path: Path) -> None:
    header = USE_VALUE_HEADER[:-1]
    with pytest.raises(DataValidationError, match="missing columns"):
        load_use_value_records(write_csv(tmp_path / "m.csv", header, [["1"] * len(header)]))
    row = ["2026", "2025", "1", "00123", "", "DESC", "100000", "2000"]
    with pytest.raises(DataValidationError, match="empty value"):
        load_use_value_records(write_csv(tmp_path / "e.csv", USE_VALUE_HEADER, [row]))


def test_every_catalog_vehicle_matches_exactly_one_tax_record(
    mock_vehicles: tuple[Vehicle, ...], tax_records: tuple[UseValueRecord, ...]
) -> None:
    index = UseValueIndex(tax_records)
    for vehicle in mock_vehicles:
        record = index.find_for_vehicle(vehicle, TAX_YEAR)
        assert mismatched_fields(vehicle, record) == (), vehicle.vehicle_id


def test_reference_file_is_the_expected_size(tax_records: tuple[UseValueRecord, ...]) -> None:
    assert len(tax_records) == 77988
    assert (MOCK_DIR / "vehicle-value-of-use.csv").exists()
