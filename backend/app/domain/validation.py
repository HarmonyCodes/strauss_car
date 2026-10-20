from decimal import Decimal

from app.domain.errors import DomainValidationError


def require_decimal(
    name: str, value: object, *, minimum: Decimal = Decimal(0), maximum: Decimal | None = None
) -> Decimal:
    """Validate a Decimal input. Floats are rejected so binary rounding never enters money."""
    if isinstance(value, bool) or not isinstance(value, Decimal):
        raise DomainValidationError(f"{name} must be a Decimal, got {type(value).__name__}")
    if not value.is_finite():
        raise DomainValidationError(f"{name} must be a finite number")
    if value < minimum:
        raise DomainValidationError(f"{name} must be at least {minimum}, got {value}")
    if maximum is not None and value > maximum:
        raise DomainValidationError(f"{name} must be at most {maximum}, got {value}")
    return value
