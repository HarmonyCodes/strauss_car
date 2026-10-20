from pathlib import Path

import pytest
from helpers import MOCK_DIR, synthetic_rules_dict, write_json

from app.domain.models import Occupation, Vehicle
from app.domain.rules import RulesConfig
from app.domain.use_value import UseValueRecord
from app.ingestion.catalog_loader import load_vehicle_catalog
from app.ingestion.occupations_loader import load_occupations
from app.ingestion.rules_loader import load_rules
from app.ingestion.use_value_loader import load_use_value_records


@pytest.fixture(scope="session")
def mock_rules() -> RulesConfig:
    return load_rules(MOCK_DIR / "car-rules.mock.json")


@pytest.fixture(scope="session")
def mock_vehicles(mock_rules: RulesConfig) -> tuple[Vehicle, ...]:
    return load_vehicle_catalog(MOCK_DIR / "vehicle_catalog.csv", mock_rules)


@pytest.fixture(scope="session")
def mock_occupations(mock_rules: RulesConfig) -> tuple[Occupation, ...]:
    return load_occupations(MOCK_DIR / "occupations.csv", mock_rules)


@pytest.fixture(scope="session")
def tax_records() -> tuple[UseValueRecord, ...]:
    path = MOCK_DIR / "vehicle-value-of-use.csv"
    if not path.exists():
        pytest.skip("reference file vehicle-value-of-use.csv is not present (kept out of Git)")
    return load_use_value_records(path)


@pytest.fixture
def synthetic_rules(tmp_path: Path) -> RulesConfig:
    return load_rules(write_json(tmp_path / "rules.json", synthetic_rules_dict()))
