from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.errors import register_error_handlers
from app.api.health import router as health_router
from app.api.scenarios import router as scenarios_router
from app.application.comparison_service import ComparisonService
from app.application.reference_data import load_reference_data
from app.config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # Loaded once; invalid reference data fails startup instead of failing requests later.
        app.state.comparison_service = ComparisonService(load_reference_data(resolved))
        yield

    app = FastAPI(title="Strauss Car Advisor", lifespan=lifespan)
    register_error_handlers(app)
    app.include_router(health_router)
    app.include_router(scenarios_router)
    return app


app = create_app()
