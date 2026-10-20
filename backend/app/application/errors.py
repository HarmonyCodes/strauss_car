from app.domain.errors import DomainValidationError


class UnknownReferenceError(DomainValidationError):
    """A request referred to a vehicle or occupation that is not in the loaded reference data."""
