from decimal import Decimal

import pytest

from app.domain.rules import PensionCreditParams, RulesConfig, SocialChargeParams, TaxBracket
from app.domain.tax import (
    income_tax_before_credits,
    pension_credit,
    social_charge,
    taxable_income_for_tax,
)

D = Decimal

BRACKETS = (
    TaxBracket(upper_limit=D(1000), rate=D("0.1")),
    TaxBracket(upper_limit=D(2000), rate=D("0.2")),
    TaxBracket(upper_limit=None, rate=D("0.3")),
)
NI = SocialChargeParams(threshold=D(500), ceiling=D(5000), low_rate=D("0.01"), high_rate=D("0.05"))
HEALTH = SocialChargeParams(
    threshold=D(500), ceiling=D(5000), low_rate=D("0.02"), high_rate=D("0.04")
)
PENSION = PensionCreditParams(
    rate=D("0.35"), max_contribution_rate=D("0.07"), income_ceiling=D(900)
)


@pytest.mark.parametrize(
    ("income", "expected"),
    [
        ("0", "0"),
        ("999", "99.9"),
        ("1000", "100"),
        ("1001", "100.2"),
        ("2000", "300"),
        ("2001", "300.3"),
        ("2500", "450"),
    ],
)
def test_tax_brackets_at_and_around_limits(income: str, expected: str) -> None:
    assert income_tax_before_credits(D(income), BRACKETS) == D(expected)


def test_tax_on_mock_rules_first_bracket_edge(mock_rules: RulesConfig) -> None:
    brackets = mock_rules.net_method.brackets
    first = brackets[0]
    assert first.upper_limit is not None
    assert income_tax_before_credits(first.upper_limit, brackets) == first.upper_limit * first.rate


def test_taxable_income_for_tax_inverts_brackets() -> None:
    assert taxable_income_for_tax(BRACKETS, D(0)) == D(0)
    assert taxable_income_for_tax(BRACKETS, D(100)) == D(1000)
    assert taxable_income_for_tax(BRACKETS, D(150)) == D(1250)
    assert taxable_income_for_tax(BRACKETS, D(450)) == D(2500)


@pytest.mark.parametrize(
    ("base", "ni", "health"),
    [
        ("0", "0", "0"),
        ("500", "5", "10"),
        ("1000", "30", "30"),
        ("5000", "230", "190"),
        ("6000", "230", "190"),
    ],
)
def test_social_charges_thresholds_and_ceilings(base: str, ni: str, health: str) -> None:
    assert social_charge(D(base), NI) == D(ni)
    assert social_charge(D(base), HEALTH) == D(health)


@pytest.mark.parametrize(
    ("income", "contribution", "expected"),
    [
        ("1000", "60", "21"),  # below the 63 cap: 60 * 0.35
        ("1000", "100", "22.05"),  # contribution above 63 is capped to 63
        ("500", "30", "10.5"),
        ("500", "35", "12.25"),
        ("0", "0", "0"),
    ],
)
def test_pension_credit_rate_and_income_ceiling(
    income: str, contribution: str, expected: str
) -> None:
    assert pension_credit(D(income), D(contribution), PENSION) == D(expected)
