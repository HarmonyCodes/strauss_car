import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.application.errors import UnknownReferenceError
from app.domain.errors import DomainValidationError, UnsupportedRuleError, VehicleMatchError

logger = logging.getLogger(__name__)


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


async def _unsupported_rule(_: Request, exc: Exception) -> JSONResponse:
    logger.error("unsupported rule configuration: %s", type(exc).__name__)
    return _error(500, "rules_not_supported", "The loaded rules cannot be calculated safely.")


async def _vehicle_match(_: Request, exc: Exception) -> JSONResponse:
    return _error(409, "vehicle_not_uniquely_identified", str(exc))


async def _unknown_reference(_: Request, exc: Exception) -> JSONResponse:
    return _error(422, "unknown_reference", str(exc))


async def _domain_validation(_: Request, exc: Exception) -> JSONResponse:
    return _error(422, "invalid_scenario", str(exc))


async def _unexpected(_: Request, exc: Exception) -> JSONResponse:
    # Only the exception type is logged: messages and tracebacks might contain employee data.
    logger.error("unhandled error: %s", type(exc).__name__)
    return _error(500, "internal_error", "An internal error occurred.")


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(UnsupportedRuleError, _unsupported_rule)
    app.add_exception_handler(VehicleMatchError, _vehicle_match)
    app.add_exception_handler(UnknownReferenceError, _unknown_reference)
    app.add_exception_handler(DomainValidationError, _domain_validation)
    app.add_exception_handler(Exception, _unexpected)
