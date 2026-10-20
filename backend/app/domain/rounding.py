from decimal import ROUND_HALF_UP, Decimal


def round_to_shekel(amount: Decimal) -> Decimal:
    """Display-only rounding to a whole shekel (half rounds away from zero).

    The rules specify shekel rounding for display but not the tie-breaking mode; half-up is the
    documented choice here. Calculations never call this function.
    """
    return amount.quantize(Decimal(1), rounding=ROUND_HALF_UP)
