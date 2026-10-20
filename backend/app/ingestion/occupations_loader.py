from decimal import Decimal
from pathlib import Path

from app.domain.models import Occupation
from app.domain.rules import RulesConfig
from app.ingestion.csv_table import CsvRow, read_csv_rows
from app.ingestion.errors import DataValidationError

COL_NAME = "עיסוק"
COL_GROUP = "קבוצת זכאות"
COL_CAR_MANDATORY = "רכב חובה"
COL_CAN_WAIVE = "מותר לוותר"
COL_MAINTENANCE = "אחזקת רכב בוויתור (₪)"

_COLUMNS = (COL_NAME, COL_GROUP, COL_CAR_MANDATORY, COL_CAN_WAIVE, COL_MAINTENANCE)
_YES = "כן"
_NO = "לא"


def load_occupations(path: Path, rules: RulesConfig) -> tuple[Occupation, ...]:
    occupations = [_parse_occupation(row, rules) for row in read_csv_rows(path, _COLUMNS)]
    if not occupations:
        raise DataValidationError(f"{path.name}: no occupations found")
    names = [occupation.name for occupation in occupations]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise DataValidationError(f"{path.name}: duplicate occupations: {duplicates}")
    return tuple(occupations)


def _parse_occupation(row: CsvRow, rules: RulesConfig) -> Occupation:
    name = row.values[COL_NAME]
    group = row.values[COL_GROUP]
    if group not in rules.group_order:
        raise DataValidationError(
            f"{row.where}: unknown eligibility group {group!r} for {name!r}; expected one of "
            f"{list(rules.group_order)}"
        )
    car_mandatory = _yes_no(row, COL_CAR_MANDATORY)
    can_waive = _yes_no(row, COL_CAN_WAIVE)
    maintenance = row.decimal(COL_MAINTENANCE)
    if car_mandatory == can_waive:
        raise DataValidationError(
            f"{row.where}: {name!r} must have exactly one of 'car mandatory' and 'may waive'"
        )
    if not can_waive and maintenance != Decimal(0):
        raise DataValidationError(
            f"{row.where}: {name!r} cannot waive but has waiver maintenance {maintenance}"
        )
    return Occupation(
        name=name,
        group=group,
        car_mandatory=car_mandatory,
        can_waive=can_waive,
        waiver_maintenance=maintenance,
    )


def _yes_no(row: CsvRow, column: str) -> bool:
    value = row.values[column]
    if value == _YES:
        return True
    if value == _NO:
        return False
    raise DataValidationError(
        f"{row.where}: column {column!r} must be {_YES!r} or {_NO!r}, found {value!r}"
    )
