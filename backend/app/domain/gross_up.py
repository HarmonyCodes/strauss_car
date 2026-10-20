from collections.abc import Callable, Iterable
from decimal import Decimal

from app.domain.errors import DomainValidationError


def solve_gross_up(
    net_increase: Decimal,
    net_at: Callable[[Decimal], Decimal],
    breakpoints: Iterable[Decimal],
) -> Decimal:
    """Taxable amount G such that net_at(G) - net_at(0) equals `net_increase` exactly.

    `net_at` must be continuous, piecewise linear and increasing in G, with kinks only at the given
    breakpoints. Linear interpolation inside the matching segment then gives the exact answer
    without any search tolerance or intermediate rounding.
    """
    if net_increase == 0:
        return Decimal(0)
    points = sorted({Decimal(0)} | {p for p in breakpoints if p > 0})
    values = [net_at(p) for p in points]
    goal = values[0] + net_increase
    for index in range(1, len(points)):
        if values[index] >= goal:
            g0, g1 = points[index - 1], points[index]
            n0, n1 = values[index - 1], values[index]
            return g0 + (goal - n0) * (g1 - g0) / (n1 - n0)
    last_point, last_value = points[-1], values[-1]
    slope = net_at(last_point + 1) - last_value
    if slope <= 0:
        raise DomainValidationError("Net income does not increase with the taxable benefit")
    return last_point + (goal - last_value) / slope
