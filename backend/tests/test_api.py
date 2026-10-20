import json
from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from helpers import (
    CATALOG_HEADER,
    OCCUPATION_HEADER,
    catalog_row,
    occupation_row,
    synthetic_rules_dict,
    write_csv,
    write_json,
)

from app.config import Settings
from app.ingestion.errors import DataValidationError
from app.main import create_app

D = Decimal
EMPLOYEE: dict[str, Any] = {
    "occupation": "can-waive",
    "base_salary": "3000",
    "credit_points": "2",
    "pension_rate": "0.06",
    "study_fund_rate": "0.025",
    "children_under_23": 0,
}


def build_settings(tmp_path: Path, rules: dict[str, Any] | None = None) -> Settings:
    write_json(tmp_path / "rules.json", rules or synthetic_rules_dict())
    write_csv(
        tmp_path / "catalog.csv",
        CATALOG_HEADER,
        [
            catalog_row(
                "V-1", **{"שווי שימוש חודשי": "400", "השתתפות עובד ברירת מחדל (דמה)": "50"}
            ),
            catalog_row(
                "V-E",
                **{
                    "הנעה": "חשמלי",
                    "שווי שימוש חודשי": "400",
                    "השתתפות עובד ברירת מחדל (דמה)": "0",
                },
            ),
            catalog_row("V-PLUG", **{"הנעה": "פלאג-אין"}),
            catalog_row("V-HIGH", **{"קבוצה": "ב"}),
            catalog_row(
                "V-FAM",
                **{
                    "קבוצה": "משפחתי",
                    "שווי שימוש חודשי": "500",
                    "עלות חודשית לחברה (דמה)": "1800",
                    "השתתפות עובד ברירת מחדל (דמה)": "999",
                },
            ),
        ],
    )
    write_csv(
        tmp_path / "occupations.csv",
        OCCUPATION_HEADER,
        [
            occupation_row("can-waive", **{"אחזקת רכב בוויתור (₪)": "1200"}),
            occupation_row(
                "mandatory",
                **{"רכב חובה": "כן", "מותר לוותר": "לא", "אחזקת רכב בוויתור (₪)": "0"},
            ),
        ],
    )
    return Settings(
        data_dir=tmp_path,
        rules_file="rules.json",
        catalog_file="catalog.csv",
        occupations_file="occupations.csv",
    )


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    with TestClient(create_app(build_settings(tmp_path))) as test_client:
        yield test_client


def body(current: dict[str, Any], alternative: dict[str, Any], **overrides: Any) -> dict[str, Any]:
    return {**EMPLOYEE, "current": current, "alternative": alternative, **overrides}


def test_options_lists_reference_data(client: TestClient) -> None:
    response = client.get("/api/v1/options")
    assert response.status_code == 200
    data = response.json()
    assert data["rules_version"] == "test-1"
    assert data["groups"] == [
        {"group": "א", "monthly_budget": "1000"},
        {"group": "ב", "monthly_budget": "2000"},
        {"group": "ג", "monthly_budget": "3000"},
    ]
    assert data["family_track"] == {
        "min_children": 4,
        "child_age_limit_exclusive": 23,
        "vehicle_ids": ["V-FAM"],
    }
    assert [v["vehicle_id"] for v in data["vehicles"]] == [
        "V-1",
        "V-E",
        "V-PLUG",
        "V-HIGH",
        "V-FAM",
    ]
    electric = {v["vehicle_id"]: v["is_electric"] for v in data["vehicles"]}
    assert electric == {"V-1": False, "V-E": True, "V-PLUG": False, "V-HIGH": False, "V-FAM": False}
    occupations = {o["name"]: o for o in data["occupations"]}
    assert occupations["can-waive"]["can_waive"] is True
    assert occupations["mandatory"]["can_waive"] is False
    assert occupations["mandatory"]["car_mandatory"] is True
    assert data["disclaimer"]


def test_options_do_not_expose_internal_data(client: TestClient, tmp_path: Path) -> None:
    text = client.get("/api/v1/options").text
    assert str(tmp_path) not in text
    assert "source_note" not in text
    assert "manufacturer_code" not in text
    assert "brackets" not in text


def test_compare_two_vehicles(client: TestClient) -> None:
    response = client.post(
        "/api/v1/scenarios/compare", json=body({"vehicle_id": "V-1"}, {"vehicle_id": "V-E"})
    )
    assert response.status_code == 200
    data = response.json()
    assert data["rules_version"] == "test-1"
    assert data["tax_table_year"] == 2025
    assert data["current"]["vehicle_id"] == "V-1"
    assert data["alternative"]["vehicle_id"] == "V-E"
    assert data["alternative"]["electric_net_bonus"] == "100"
    assert D(data["alternative"]["electric_gross_up"]) > 100
    assert data["assumptions"]
    assert "המחשה" in data["disclaimer"]


def test_compare_vehicle_to_waiver_and_difference_direction(client: TestClient) -> None:
    response = client.post(
        "/api/v1/scenarios/compare", json=body({"vehicle_id": "V-1"}, {"waive": True})
    )
    assert response.status_code == 200
    data = response.json()
    assert data["current"]["is_waiver"] is False
    assert data["alternative"]["is_waiver"] is True
    assert data["alternative"]["waiver_maintenance"] == "1200"
    # Values were derived by hand in the domain tests (net 1921.05 and 2859.05).
    assert data["current"]["net_salary"] == "1921.05"
    assert data["alternative"]["net_salary"] == "2859.05"
    assert data["net_difference"] == "938"
    assert data["net_difference_rounded"] == "938"

    reverse = client.post(
        "/api/v1/scenarios/compare", json=body({"waive": True}, {"vehicle_id": "V-1"})
    ).json()
    assert D(reverse["net_difference"]) == -D(data["net_difference"])


def test_family_track_uses_server_side_rules(client: TestClient) -> None:
    response = client.post(
        "/api/v1/scenarios/compare",
        json=body({"vehicle_id": "V-1"}, {"vehicle_id": "V-FAM"}, children_under_23=4),
    )
    assert response.status_code == 200
    assert response.json()["alternative"]["participation"] == "1399"


@pytest.mark.parametrize(("children", "status"), [(3, 422), (4, 200)])
def test_family_vehicle_children_boundary(client: TestClient, children: int, status: int) -> None:
    response = client.post(
        "/api/v1/scenarios/compare",
        json=body({"vehicle_id": "V-1"}, {"vehicle_id": "V-FAM"}, children_under_23=children),
    )
    assert response.status_code == status
    if status == 422:
        assert response.json()["error"]["code"] == "invalid_scenario"


def test_money_is_serialized_as_decimal_strings(client: TestClient) -> None:
    data = client.post(
        "/api/v1/scenarios/compare", json=body({"vehicle_id": "V-1"}, {"vehicle_id": "V-E"})
    ).json()
    for scenario in (data["current"], data["alternative"]):
        for key, value in scenario.items():
            if key in {"vehicle_id", "is_waiver"}:
                continue
            assert isinstance(value, str), key
            assert "e" not in value.lower(), key
            D(value)
    assert isinstance(data["net_difference"], str)
    # The gross-up is not a terminating decimal and must keep full precision, not float digits.
    assert len(data["alternative"]["electric_gross_up"].split(".")[1]) > 17


def test_decimal_input_accepts_numbers_and_strings(client: TestClient) -> None:
    as_number = body({"vehicle_id": "V-1"}, {"waive": True}, base_salary=3000.5)
    as_string = body({"vehicle_id": "V-1"}, {"waive": True}, base_salary="3000.5")
    first = client.post("/api/v1/scenarios/compare", json=as_number)
    second = client.post("/api/v1/scenarios/compare", json=as_string)
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()


def test_unknown_vehicle_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/v1/scenarios/compare", json=body({"vehicle_id": "NOPE"}, {"waive": True})
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "unknown_reference"
    assert "NOPE" in response.json()["error"]["message"]


def test_unknown_occupation_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/v1/scenarios/compare",
        json=body({"vehicle_id": "V-1"}, {"waive": True}, occupation="nobody"),
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "unknown_reference"


@pytest.mark.parametrize(
    ("override", "field"),
    [
        ({"base_salary": "-1"}, "base_salary"),
        ({"base_salary": "NaN"}, "base_salary"),
        ({"base_salary": "abc"}, "base_salary"),
        ({"pension_rate": "1.5"}, "pension_rate"),
        ({"study_fund_rate": "-0.1"}, "study_fund_rate"),
        ({"credit_points": "-2"}, "credit_points"),
        ({"children_under_23": -1}, "children_under_23"),
        ({"children_under_23": 31}, "children_under_23"),
        ({"children_under_23": 2.5}, "children_under_23"),
        ({"child_ages": [1, 2]}, "child_ages"),
        ({"occupation": ""}, "occupation"),
    ],
)
def test_invalid_values_rejected(client: TestClient, override: dict[str, Any], field: str) -> None:
    response = client.post(
        "/api/v1/scenarios/compare",
        json=body({"vehicle_id": "V-1"}, {"waive": True}, **override),
    )
    assert response.status_code == 422
    assert field in json.dumps(response.json()["detail"])


@pytest.mark.parametrize("missing", ["occupation", "base_salary", "credit_points", "current"])
def test_missing_required_field_rejected(client: TestClient, missing: str) -> None:
    payload = body({"vehicle_id": "V-1"}, {"waive": True})
    del payload[missing]
    response = client.post("/api/v1/scenarios/compare", json=payload)
    assert response.status_code == 422
    assert missing in json.dumps(response.json()["detail"])


@pytest.mark.parametrize("choice", [{}, {"vehicle_id": "V-1", "waive": True}, {"waive": False}])
def test_choice_needs_exactly_one_option(client: TestClient, choice: dict[str, Any]) -> None:
    response = client.post("/api/v1/scenarios/compare", json=body(choice, {"waive": True}))
    assert response.status_code == 422


def test_client_cannot_override_budget_or_participation(client: TestClient) -> None:
    for extra in ({"budget": "99999"}, {"participation": "0"}, {"group": "ג"}):
        response = client.post(
            "/api/v1/scenarios/compare",
            json=body({"vehicle_id": "V-1"}, {"waive": True}, **extra),
        )
        assert response.status_code == 422, extra


def test_waiver_rejected_when_occupation_cannot_waive(client: TestClient) -> None:
    response = client.post(
        "/api/v1/scenarios/compare",
        json=body({"vehicle_id": "V-1"}, {"waive": True}, occupation="mandatory"),
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_scenario"
    assert "waive" in response.json()["error"]["message"]


@pytest.mark.parametrize(
    ("vehicle_id", "message_part"),
    [("V-HIGH", "not available to group"), ("V-FAM", "Family-track eligibility")],
)
def test_vehicle_not_allowed_for_employee_rejected(
    client: TestClient, vehicle_id: str, message_part: str
) -> None:
    response = client.post(
        "/api/v1/scenarios/compare",
        json=body({"vehicle_id": "V-1"}, {"vehicle_id": vehicle_id}, children_under_23=3),
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_scenario"
    message = response.json()["error"]["message"]
    assert message_part in message
    if vehicle_id == "V-FAM":
        assert "group" not in message


def test_zero_gross_salary_rejected_by_domain(client: TestClient) -> None:
    response = client.post(
        "/api/v1/scenarios/compare",
        json=body({"vehicle_id": "V-1"}, {"waive": True}, base_salary="0"),
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_scenario"


def test_unsupported_rules_return_generic_error(tmp_path: Path) -> None:
    rules = synthetic_rules_dict()
    rules["netMethod"]["participation"]["reducesValueOfUse"] = True
    with TestClient(create_app(build_settings(tmp_path, rules))) as test_client:
        response = test_client.post(
            "/api/v1/scenarios/compare", json=body({"vehicle_id": "V-1"}, {"waive": True})
        )
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "rules_not_supported"
    assert "reducesValueOfUse" not in response.text
    assert "Traceback" not in response.text


def test_startup_fails_when_reference_data_is_missing(tmp_path: Path) -> None:
    settings = build_settings(tmp_path)
    (tmp_path / "catalog.csv").unlink()
    with pytest.raises((OSError, DataValidationError)), TestClient(create_app(settings)):
        pass
