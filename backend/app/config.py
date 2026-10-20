from pathlib import Path

from pydantic import BaseModel, ConfigDict

_DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "mock"


class Settings(BaseModel):
    """Locations of the reference data files. Contains no secrets."""

    model_config = ConfigDict(frozen=True)

    data_dir: Path = _DEFAULT_DATA_DIR
    rules_file: str = "car-rules.mock.json"
    catalog_file: str = "vehicle_catalog.csv"
    occupations_file: str = "occupations.csv"

    @property
    def rules_path(self) -> Path:
        return self.data_dir / self.rules_file

    @property
    def catalog_path(self) -> Path:
        return self.data_dir / self.catalog_file

    @property
    def occupations_path(self) -> Path:
        return self.data_dir / self.occupations_file
