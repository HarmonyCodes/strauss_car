from collections.abc import Sequence
from decimal import Decimal

from app.domain.rules import PensionCreditParams, SocialChargeParams, TaxBracket

_ZERO = Decimal(0)


def income_tax_before_credits(taxable_income: Decimal, brackets: Sequence[TaxBracket]) -> Decimal:
    """Progressive tax; each bracket's upper limit is the cumulative income where it ends."""
    tax = _ZERO
    lower = _ZERO
    for bracket in brackets:
        upper = bracket.upper_limit
        if upper is None or taxable_income <= upper:
            tax += max(_ZERO, taxable_income - lower) * bracket.rate
            break
        tax += (upper - lower) * bracket.rate
        lower = upper
    return tax


def taxable_income_for_tax(brackets: Sequence[TaxBracket], tax: Decimal) -> Decimal | None:
    """Income at which the pre-credit tax equals `tax`, or None if it is never reached."""
    if tax <= _ZERO:
        return _ZERO
    remaining = tax
    lower = _ZERO
    for bracket in brackets:
        upper = bracket.upper_limit
        if upper is None:
            return lower + remaining / bracket.rate if bracket.rate > _ZERO else None
        band_tax = (upper - lower) * bracket.rate
        if bracket.rate > _ZERO and remaining <= band_tax:
            return lower + remaining / bracket.rate
        remaining -= band_tax
        lower = upper
    return None


def social_charge(base: Decimal, params: SocialChargeParams) -> Decimal:
    """Two-tier charge: low rate up to the threshold, high rate from there up to the ceiling."""
    low_part = min(base, params.threshold) * params.low_rate
    high_part = max(_ZERO, min(base, params.ceiling) - params.threshold) * params.high_rate
    return low_part + high_part


def pension_credit(
    pensionable_income: Decimal, employee_contribution: Decimal, params: PensionCreditParams
) -> Decimal:
    """Credit on the employee pension contribution, up to a share of the capped income."""
    qualifying_income = min(pensionable_income, params.income_ceiling)
    creditable = min(employee_contribution, params.max_contribution_rate * qualifying_income)
    return creditable * params.rate
