from decimal import Decimal
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, model_validator

from app.application.comparison_service import CarChoice, ComparisonInput
from app.domain.models import Occupation, Vehicle
from app.domain.rounding import round_to_shekel
from app.domain.scenario import ComparisonResult, ScenarioResult

DISCLAIMER = (
    "נתוני המחשה בלבד: פרמטרי המס והנטו הם נתוני דמה ואינם מסים רשמיים. "
    "התוצאה אינה ייעוץ שכר או מיסוי."
)


def _plain(value: Decimal) -> str:
    # format(..., "f") never rounds, unlike normalize(), which rounds to the active context
    # precision. Trailing fractional zeros are stripped as text; whole digits are untouched.
    if value == 0:
        return "0"
    text = format(value, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


Amount = Annotated[Decimal, PlainSerializer(_plain, return_type=str, when_used="json")]

# Technical sanity bounds against absurd input; they are not business rules.
Money = Annotated[Decimal, Field(ge=0, le=Decimal(10_000_000), max_digits=12, decimal_places=2)]
Rate = Annotated[Decimal, Field(ge=0, le=1, max_digits=6, decimal_places=4)]
CreditPoints = Annotated[Decimal, Field(ge=0, le=Decimal(100), max_digits=6, decimal_places=3)]
ChildCount = Annotated[int, Field(ge=0, le=30)]


class StrictModel(BaseModel):
    # Unknown fields (e.g. a client-supplied budget or participation) are rejected, not ignored.
    model_config = ConfigDict(extra="forbid")


class CarChoiceIn(StrictModel):
    vehicle_id: str | None = Field(
        default=None, min_length=1, max_length=50, description="Catalog id, e.g. CAR-01"
    )
    waive: bool = Field(default=False, description="True to waive the car instead of choosing one")

    @model_validator(mode="after")
    def _exactly_one(self) -> Self:
        if self.waive == (self.vehicle_id is not None):
            raise ValueError("Provide exactly one of vehicle_id or waive=true")
        return self

    def to_choice(self) -> CarChoice:
        return CarChoice(vehicle_id=None if self.waive else self.vehicle_id)


class CompareRequest(StrictModel):
    occupation: str = Field(min_length=1, max_length=100, description="Occupation name")
    base_salary: Money
    commissions: Money = Decimal(0)
    bonus: Money = Decimal(0)
    credit_points: CreditPoints
    pension_rate: Rate
    study_fund_rate: Rate
    children_under_23: ChildCount = Field(
        default=0, description="Number of children who have not yet turned 23"
    )
    current: CarChoiceIn
    alternative: CarChoiceIn

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "occupation": "מפתח/ת תוכנה",
                    "base_salary": "15000",
                    "commissions": "0",
                    "bonus": "0",
                    "credit_points": "2.25",
                    "pension_rate": "0.06",
                    "study_fund_rate": "0.025",
                    "children_under_23": 0,
                    "current": {"vehicle_id": "CAR-05"},
                    "alternative": {"vehicle_id": "CAR-06"},
                }
            ]
        },
    )

    def to_input(self) -> ComparisonInput:
        return ComparisonInput(
            occupation_name=self.occupation,
            base_salary=self.base_salary,
            commissions=self.commissions,
            bonus=self.bonus,
            credit_points=self.credit_points,
            pension_rate=self.pension_rate,
            study_fund_rate=self.study_fund_rate,
            children_under_23=self.children_under_23,
            current=self.current.to_choice(),
            alternative=self.alternative.to_choice(),
        )


class ScenarioOut(BaseModel):
    """Exact (unrounded) monthly amounts as decimal strings, plus a whole-shekel display value."""

    vehicle_id: str | None
    is_waiver: bool
    gross_salary: Amount
    use_value: Amount
    waiver_maintenance: Amount
    electric_net_bonus: Amount
    electric_gross_up: Amount
    taxable_income: Amount
    tax_before_credits: Amount
    credit_points_credit: Amount
    pension_credit: Amount
    income_tax: Amount
    national_insurance: Amount
    health_insurance: Amount
    pension_contribution: Amount
    study_fund_contribution: Amount
    participation: Amount
    net_before_electric_benefit: Amount
    net_salary: Amount
    net_salary_rounded: Amount

    @classmethod
    def from_result(cls, result: ScenarioResult) -> Self:
        return cls(
            vehicle_id=result.vehicle_id,
            is_waiver=result.is_waiver,
            gross_salary=result.gross_salary,
            use_value=result.use_value,
            waiver_maintenance=result.waiver_maintenance,
            electric_net_bonus=result.electric_net_bonus,
            electric_gross_up=result.electric_gross_up,
            taxable_income=result.taxable_income,
            tax_before_credits=result.tax_before_credits,
            credit_points_credit=result.credit_points_credit,
            pension_credit=result.pension_credit,
            income_tax=result.income_tax,
            national_insurance=result.national_insurance,
            health_insurance=result.health_insurance,
            pension_contribution=result.pension_contribution,
            study_fund_contribution=result.study_fund_contribution,
            participation=result.participation,
            net_before_electric_benefit=result.net_before_electric_benefit,
            net_salary=result.net_salary,
            net_salary_rounded=round_to_shekel(result.net_salary),
        )


class CompareResponse(BaseModel):
    rules_version: str
    tax_table_year: int
    current: ScenarioOut
    alternative: ScenarioOut
    net_difference: Amount = Field(description="alternative net minus current net")
    net_difference_rounded: Amount
    assumptions: list[str]
    disclaimer: str = DISCLAIMER

    @classmethod
    def from_result(cls, result: ComparisonResult) -> Self:
        return cls(
            rules_version=result.rules_version,
            tax_table_year=result.alternative.tax_table_year,
            current=ScenarioOut.from_result(result.current),
            alternative=ScenarioOut.from_result(result.alternative),
            net_difference=result.net_difference,
            net_difference_rounded=round_to_shekel(result.net_difference),
            assumptions=list(result.alternative.assumptions),
        )


class GroupOut(BaseModel):
    group: str
    monthly_budget: Amount


class VehicleOut(BaseModel):
    vehicle_id: str
    track: str
    group: str | None
    brand: str
    model_name: str
    registration_year: int
    drive: str
    is_electric: bool
    list_price: Amount
    monthly_use_value: Amount
    monthly_company_cost: Amount
    default_participation: Amount

    @classmethod
    def from_vehicle(cls, vehicle: Vehicle) -> Self:
        return cls(
            vehicle_id=vehicle.vehicle_id,
            track=vehicle.track.value,
            group=vehicle.group,
            brand=vehicle.brand,
            model_name=vehicle.model_name,
            registration_year=vehicle.registration_year,
            drive=vehicle.drive.value,
            is_electric=vehicle.is_electric,
            list_price=vehicle.list_price,
            monthly_use_value=vehicle.monthly_use_value,
            monthly_company_cost=vehicle.monthly_company_cost,
            default_participation=vehicle.default_participation,
        )


class OccupationOut(BaseModel):
    name: str
    group: str
    car_mandatory: bool
    can_waive: bool
    waiver_maintenance: Amount

    @classmethod
    def from_occupation(cls, occupation: Occupation) -> Self:
        return cls(
            name=occupation.name,
            group=occupation.group,
            car_mandatory=occupation.car_mandatory,
            can_waive=occupation.can_waive,
            waiver_maintenance=occupation.waiver_maintenance,
        )


class FamilyTrackOut(BaseModel):
    min_children: int
    child_age_limit_exclusive: int
    vehicle_ids: list[str]


class OptionsResponse(BaseModel):
    rules_version: str
    groups: list[GroupOut]
    family_track: FamilyTrackOut
    vehicles: list[VehicleOut]
    occupations: list[OccupationOut]
    disclaimer: str = DISCLAIMER
