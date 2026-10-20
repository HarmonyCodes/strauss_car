from pathlib import Path

from app.domain.use_value import UseValueRecord
from app.ingestion.csv_table import read_csv_rows
from app.ingestion.errors import DataValidationError

COL_TAX_YEAR = "שנת מס"
COL_REGISTRATION_YEAR = "שנת רישום"
COL_VEHICLE_TYPE_CODE = "קוד סוג רכב"
COL_MANUFACTURER_CODE = "קוד תוצר"
COL_MODEL_CODE = "קוד דגם"
COL_MODEL_DESCRIPTION = "תאור דגם"
COL_LIST_PRICE = "מחיר מחירון"
COL_USE_VALUE = "שווי שימוש"

_COLUMNS = (
    COL_TAX_YEAR,
    COL_REGISTRATION_YEAR,
    COL_VEHICLE_TYPE_CODE,
    COL_MANUFACTURER_CODE,
    COL_MODEL_CODE,
    COL_MODEL_DESCRIPTION,
    COL_LIST_PRICE,
    COL_USE_VALUE,
)


def load_use_value_records(path: Path) -> tuple[UseValueRecord, ...]:
    """Load the tax-authority use-value file; the file itself is never modified.

    The full source key (including vehicle-type code) must be unique across the file.
    """
    records: list[UseValueRecord] = []
    seen: set[tuple[int, int, str, str, str, str]] = set()
    for row in read_csv_rows(path, _COLUMNS):
        record = UseValueRecord(
            tax_year=row.integer(COL_TAX_YEAR),
            registration_year=row.integer(COL_REGISTRATION_YEAR),
            vehicle_type_code=row.code(COL_VEHICLE_TYPE_CODE),
            manufacturer_code=row.code(COL_MANUFACTURER_CODE),
            model_code=row.code(COL_MODEL_CODE),
            model_description=row.values[COL_MODEL_DESCRIPTION],
            list_price=row.decimal(COL_LIST_PRICE),
            monthly_use_value=row.decimal(COL_USE_VALUE),
        )
        key = (
            record.tax_year,
            record.registration_year,
            record.vehicle_type_code,
            record.manufacturer_code,
            record.model_code,
            record.model_description,
        )
        if key in seen:
            raise DataValidationError(f"{row.where}: duplicate use-value key {key}")
        seen.add(key)
        records.append(record)
    if not records:
        raise DataValidationError(f"{path.name}: no records found")
    return tuple(records)
