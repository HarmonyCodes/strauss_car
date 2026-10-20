from pathlib import Path

from app.domain.models import DriveType, Vehicle, VehicleTrack
from app.domain.rules import RulesConfig
from app.ingestion.csv_table import CsvRow, read_csv_rows
from app.ingestion.errors import DataValidationError

FAMILY_GROUP_LABEL = "משפחתי"

COL_ID = "מזהה"
COL_GROUP = "קבוצה"
COL_BRAND = "תוצר"
COL_MANUFACTURER_CODE = "קוד תוצר"
COL_MODEL_NAME = "דגם (כינוי מסחרי)"
COL_MODEL_CODE = "קוד דגם"
COL_MODEL_DESCRIPTION = "תאור דגם"
COL_REGISTRATION_YEAR = "שנת רישום"
COL_DRIVE = "הנעה"
COL_LIST_PRICE = "מחיר מחירון"
COL_USE_VALUE = "שווי שימוש חודשי"
COL_COMPANY_COST = "עלות חודשית לחברה (דמה)"
COL_PARTICIPATION = "השתתפות עובד ברירת מחדל (דמה)"

_COLUMNS = (
    COL_ID,
    COL_GROUP,
    COL_BRAND,
    COL_MANUFACTURER_CODE,
    COL_MODEL_NAME,
    COL_MODEL_CODE,
    COL_MODEL_DESCRIPTION,
    COL_REGISTRATION_YEAR,
    COL_DRIVE,
    COL_LIST_PRICE,
    COL_USE_VALUE,
    COL_COMPANY_COST,
    COL_PARTICIPATION,
)


def load_vehicle_catalog(path: Path, rules: RulesConfig) -> tuple[Vehicle, ...]:
    """Load the vehicle catalog.

    A vehicle is on the family track when its id is listed in the rules; its catalog group must
    then be the family label. Every other vehicle must belong to a regular budget group.
    """
    vehicles = [_parse_vehicle(row, rules) for row in read_csv_rows(path, _COLUMNS)]
    if not vehicles:
        raise DataValidationError(f"{path.name}: no vehicles found")
    _check_unique(vehicles, path.name)
    missing = rules.family_track.car_ids - {vehicle.vehicle_id for vehicle in vehicles}
    if missing:
        raise DataValidationError(
            f"{path.name}: family-track vehicles missing from catalog: {sorted(missing)}"
        )
    return tuple(vehicles)


def _parse_vehicle(row: CsvRow, rules: RulesConfig) -> Vehicle:
    vehicle_id = row.values[COL_ID]
    group_label = row.values[COL_GROUP]
    if vehicle_id in rules.family_track.car_ids:
        if group_label != FAMILY_GROUP_LABEL:
            raise DataValidationError(
                f"{row.where}: {vehicle_id} is a family-track vehicle but its group is "
                f"{group_label!r}, expected {FAMILY_GROUP_LABEL!r}"
            )
        track, group = VehicleTrack.FAMILY, None
    else:
        if group_label not in rules.group_order:
            raise DataValidationError(
                f"{row.where}: unknown group {group_label!r}; expected one of "
                f"{list(rules.group_order)}"
            )
        track, group = VehicleTrack.REGULAR, group_label
    drive_label = row.values[COL_DRIVE]
    try:
        drive = DriveType(drive_label)
    except ValueError:
        raise DataValidationError(
            f"{row.where}: unknown drive type {drive_label!r}; expected one of "
            f"{[member.value for member in DriveType]}"
        ) from None
    return Vehicle(
        vehicle_id=vehicle_id,
        track=track,
        group=group,
        brand=row.values[COL_BRAND],
        manufacturer_code=row.code(COL_MANUFACTURER_CODE),
        model_name=row.values[COL_MODEL_NAME],
        model_code=row.code(COL_MODEL_CODE),
        model_description=row.values[COL_MODEL_DESCRIPTION],
        registration_year=row.integer(COL_REGISTRATION_YEAR),
        drive=drive,
        list_price=row.decimal(COL_LIST_PRICE),
        monthly_use_value=row.decimal(COL_USE_VALUE),
        monthly_company_cost=row.decimal(COL_COMPANY_COST),
        default_participation=row.decimal(COL_PARTICIPATION),
    )


def _check_unique(vehicles: list[Vehicle], source: str) -> None:
    seen_ids: set[str] = set()
    seen_keys: set[tuple[int, str, str, str]] = set()
    for vehicle in vehicles:
        if vehicle.vehicle_id in seen_ids:
            raise DataValidationError(f"{source}: duplicate vehicle id {vehicle.vehicle_id!r}")
        seen_ids.add(vehicle.vehicle_id)
        key = (
            vehicle.registration_year,
            vehicle.manufacturer_code,
            vehicle.model_code,
            vehicle.model_description,
        )
        if key in seen_keys:
            raise DataValidationError(
                f"{source}: duplicate vehicle key {key} (vehicle {vehicle.vehicle_id})"
            )
        seen_keys.add(key)
