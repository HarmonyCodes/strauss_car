class DomainValidationError(ValueError):
    """A domain rule or input was violated."""


class UnsupportedRuleError(DomainValidationError):
    """The rules request behavior the calculation engine does not implement."""


class VehicleMatchError(DomainValidationError):
    """A vehicle could not be matched to exactly one use-value record."""


class NoVehicleMatchError(VehicleMatchError):
    """No use-value record matches the vehicle."""


class AmbiguousVehicleMatchError(VehicleMatchError):
    """More than one use-value record matches the vehicle."""
