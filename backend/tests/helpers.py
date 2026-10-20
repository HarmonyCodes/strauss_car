import copy
import csv
import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from app.domain.models import DriveType, Occupation, Vehicle, VehicleTrack
from app.domain.scenario import EmployeeProfile, SalaryComponents

MOCK_DIR = Path(__file__).resolve().parents[2] / "data" / "mock"

CATALOG_HEADER = [
    "מזהה",
    "קבוצה",
    "תוצר",
    "קוד תוצר",
    "דגם (כינוי מסחרי)",
    "קוד דגם",
    "תאור דגם",
    "שנת רישום",
    "הנעה",
    "מחיר מחירון",
    "שווי שימוש חודשי",
    "עלות חודשית לחברה (דמה)",
    "השתתפות עובד ברירת מחדל (דמה)",
]
OCCUPATION_HEADER = [
    "עיסוק",
    "קבוצת זכאות",
    "רכב חובה",
    "מותר לוותר",
    "אחזקת רכב בוויתור (₪)",
]
USE_VALUE_HEADER = [
    "שנת מס",
    "שנת רישום",
    "קוד סוג רכב",
    "קוד תוצר",
    "קוד דגם",
    "תאור דגם",
    "מחיר מחירון",
    "שווי שימוש",
]


def synthetic_rules_dict() -> dict[str, Any]:
    """Minimal valid synthetic rules, with deliberately different numbers than the mock file."""
    return copy.deepcopy(
        {
            "version": "test-1",
            "note": "synthetic test rules",
            "budgets": {"א": 1000, "ב": 2000, "ג": 3000},
            "groupOrder": ["א", "ב", "ג"],
            "chooseFrom": "own_group_or_lower",
            "electric": {"netBonus": 100, "method": "gross_up"},
            "familyTrack": {
                "minChildren": 4,
                "childMaxAge": 23,
                "cars": ["V-FAM"],
                "gapSplitEmployee": 0.5,
            },
            "waiver": {
                "allowedBy": "occupation",
                "maintenanceIsTaxable": True,
                "maintenanceIsPensionable": False,
            },
            "unusedBudget": "not_paid",
            "netMethod": {
                "basis": "monthly",
                "taxYear": 2025,
                "creditPointValue": 100,
                "brackets": [[1000, 0.1], [2000, 0.2], [None, 0.3]],
                "nationalInsurance": {
                    "threshold": 500,
                    "ceiling": 5000,
                    "lowRate": 0.01,
                    "highRate": 0.05,
                },
                "health": {"threshold": 500, "ceiling": 5000, "lowRate": 0.02, "highRate": 0.04},
                "pensionCredit": {"rate": 0.35, "maxContributionRate": 0.07, "incomeCeiling": 900},
                "contributionsBase": "gross",
                "participation": {"treatment": "net_deduction", "reducesValueOfUse": False},
                "rounding": {"during": "none", "display": "shekel"},
            },
        }
    )


def write_json(path: Path, data: object) -> Path:
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


def write_csv(path: Path, header: list[str], rows: list[list[str]]) -> Path:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)
    return path


def catalog_row(vehicle_id: str = "V-1", **overrides: str) -> list[str]:
    values = {
        "מזהה": vehicle_id,
        "קבוצה": "א",
        "תוצר": "brand",
        "קוד תוצר": "00123",
        "דגם (כינוי מסחרי)": "model",
        "קוד דגם": "00045",
        "תאור דגם": f"DESC-{vehicle_id}",
        "שנת רישום": "2025",
        "הנעה": "בנזין",
        "מחיר מחירון": "100000",
        "שווי שימוש חודשי": "2000",
        "עלות חודשית לחברה (דמה)": "900",
        "השתתפות עובד ברירת מחדל (דמה)": "50",
    }
    values.update(overrides)
    return [values[column] for column in CATALOG_HEADER]


def occupation_row(name: str = "occ", **overrides: str) -> list[str]:
    values = {
        "עיסוק": name,
        "קבוצת זכאות": "א",
        "רכב חובה": "לא",
        "מותר לוותר": "כן",
        "אחזקת רכב בוויתור (₪)": "100",
    }
    values.update(overrides)
    return [values[column] for column in OCCUPATION_HEADER]


def make_vehicle(**overrides: Any) -> Vehicle:
    fields: dict[str, Any] = {
        "vehicle_id": "V-1",
        "track": VehicleTrack.REGULAR,
        "group": "א",
        "brand": "brand",
        "manufacturer_code": "00123",
        "model_name": "model",
        "model_code": "00045",
        "model_description": "DESC",
        "registration_year": 2025,
        "drive": DriveType.PETROL,
        "list_price": Decimal(100000),
        "monthly_use_value": Decimal(2000),
        "monthly_company_cost": Decimal(900),
        "default_participation": Decimal(50),
    }
    fields.update(overrides)
    return Vehicle(**fields)


def make_occupation(**overrides: Any) -> Occupation:
    fields: dict[str, Any] = {
        "name": "occ",
        "group": "א",
        "car_mandatory": False,
        "can_waive": True,
        "waiver_maintenance": Decimal(1200),
    }
    fields.update(overrides)
    return Occupation(**fields)


def make_employee(
    *,
    base: str = "3000",
    credit_points: str = "2",
    pension_rate: str = "0.06",
    study_fund_rate: str = "0.025",
    children_under_23: int = 0,
    **occupation_overrides: Any,
) -> EmployeeProfile:
    return EmployeeProfile(
        occupation=make_occupation(**occupation_overrides),
        salary=SalaryComponents(base=Decimal(base)),
        credit_points=Decimal(credit_points),
        pension_rate=Decimal(pension_rate),
        study_fund_rate=Decimal(study_fund_rate),
        children_under_23=children_under_23,
    )
