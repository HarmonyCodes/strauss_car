from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.api.schemas import (
    CompareRequest,
    CompareResponse,
    FamilyTrackOut,
    GroupOut,
    OccupationOut,
    OptionsResponse,
    VehicleOut,
)
from app.application.comparison_service import ComparisonService

router = APIRouter(prefix="/api/v1", tags=["scenarios"])


def get_service(request: Request) -> ComparisonService:
    service: ComparisonService = request.app.state.comparison_service
    return service


ServiceDep = Annotated[ComparisonService, Depends(get_service)]


@router.get("/options", response_model=OptionsResponse)
async def get_options(service: ServiceDep) -> OptionsResponse:
    data = service.data
    rules = data.rules
    return OptionsResponse(
        rules_version=rules.version,
        groups=[
            GroupOut(group=group, monthly_budget=rules.group_budgets[group])
            for group in rules.group_order
        ],
        family_track=FamilyTrackOut(
            min_children=rules.family_track.min_children,
            child_age_limit_exclusive=rules.family_track.child_age_limit,
            vehicle_ids=sorted(rules.family_track.car_ids),
        ),
        vehicles=[VehicleOut.from_vehicle(v) for v in data.vehicles],
        occupations=[OccupationOut.from_occupation(o) for o in data.occupations],
    )


@router.post("/scenarios/compare", response_model=CompareResponse)
async def compare_scenarios_endpoint(body: CompareRequest, service: ServiceDep) -> CompareResponse:
    return CompareResponse.from_result(service.compare(body.to_input()))
