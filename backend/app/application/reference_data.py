from dataclasses import dataclass

from app.config import Settings
from app.domain.models import Occupation, Vehicle
from app.domain.rules import RulesConfig
from app.ingestion.catalog_loader import load_vehicle_catalog
from app.ingestion.occupations_loader import load_occupations
from app.ingestion.rules_loader import load_rules


@dataclass(frozen=True, slots=True)
class ReferenceData:
    """Validated, immutable reference data loaded once at startup."""

    rules: RulesConfig
    vehicles: tuple[Vehicle, ...]
    occupations: tuple[Occupation, ...]

    def vehicle(self, vehicle_id: str) -> Vehicle | None:
        return next((v for v in self.vehicles if v.vehicle_id == vehicle_id), None)

    def occupation(self, name: str) -> Occupation | None:
        return next((o for o in self.occupations if o.name == name), None)


def load_reference_data(settings: Settings) -> ReferenceData:
    rules = load_rules(settings.rules_path)
    return ReferenceData(
        rules=rules,
        vehicles=load_vehicle_catalog(settings.catalog_path, rules),
        occupations=load_occupations(settings.occupations_path, rules),
    )
