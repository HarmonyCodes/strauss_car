from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from app.domain.errors import AmbiguousVehicleMatchError, NoVehicleMatchError
from app.domain.models import Vehicle


@dataclass(frozen=True, slots=True)
class UseValueRecord:
    tax_year: int
    registration_year: int
    vehicle_type_code: str
    manufacturer_code: str
    model_code: str
    model_description: str
    list_price: Decimal
    monthly_use_value: Decimal


type _LookupKey = tuple[int, int, str, str, str]


class UseValueIndex:
    """Lookup of tax-authority use-value records.

    The approved lookup key is tax year, registration year, manufacturer code, model code and
    model description. The vehicle-type code is optional: the catalog does not carry it, and the
    model description disambiguates records that share the other codes. A lookup that does not
    resolve to exactly one record fails instead of guessing.
    """

    def __init__(self, records: Iterable[UseValueRecord]) -> None:
        self._by_key: dict[_LookupKey, list[UseValueRecord]] = defaultdict(list)
        for record in records:
            self._by_key[_key_of(record)].append(record)

    def find(
        self,
        *,
        tax_year: int,
        registration_year: int,
        manufacturer_code: str,
        model_code: str,
        model_description: str,
        vehicle_type_code: str | None = None,
    ) -> UseValueRecord:
        key = (tax_year, registration_year, manufacturer_code, model_code, model_description)
        matches = self._by_key.get(key, [])
        if vehicle_type_code is not None:
            matches = [m for m in matches if m.vehicle_type_code == vehicle_type_code]
        if not matches:
            raise NoVehicleMatchError(f"No use-value record matches key {key}")
        if len(matches) > 1:
            raise AmbiguousVehicleMatchError(
                f"{len(matches)} use-value records match key {key}; expected exactly one"
            )
        return matches[0]

    def find_for_vehicle(self, vehicle: Vehicle, tax_year: int) -> UseValueRecord:
        return self.find(
            tax_year=tax_year,
            registration_year=vehicle.registration_year,
            manufacturer_code=vehicle.manufacturer_code,
            model_code=vehicle.model_code,
            model_description=vehicle.model_description,
        )


def _key_of(record: UseValueRecord) -> _LookupKey:
    return (
        record.tax_year,
        record.registration_year,
        record.manufacturer_code,
        record.model_code,
        record.model_description,
    )


def mismatched_fields(vehicle: Vehicle, record: UseValueRecord) -> tuple[str, ...]:
    """Names of catalog values that differ from the matched tax-authority record."""
    differences: list[str] = []
    if vehicle.list_price != record.list_price:
        differences.append("list_price")
    if vehicle.monthly_use_value != record.monthly_use_value:
        differences.append("monthly_use_value")
    return tuple(differences)
