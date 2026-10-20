from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class DriveType(StrEnum):
    """Drive classification as labelled in the vehicle catalog (not the numeric tax-file code)."""

    PETROL = "בנזין"
    HYBRID = "היברידי"
    PLUG_IN = "פלאג-אין"
    ELECTRIC = "חשמלי"


class VehicleTrack(StrEnum):
    REGULAR = "regular"
    FAMILY = "family"


@dataclass(frozen=True, slots=True)
class Vehicle:
    vehicle_id: str
    track: VehicleTrack
    # Budget group of a regular vehicle; None for family-track vehicles.
    group: str | None
    brand: str
    manufacturer_code: str
    model_name: str
    model_code: str
    model_description: str
    registration_year: int
    drive: DriveType
    list_price: Decimal
    monthly_use_value: Decimal
    monthly_company_cost: Decimal
    default_participation: Decimal

    @property
    def is_electric(self) -> bool:
        return self.drive is DriveType.ELECTRIC


@dataclass(frozen=True, slots=True)
class Occupation:
    name: str
    group: str
    car_mandatory: bool
    can_waive: bool
    waiver_maintenance: Decimal
