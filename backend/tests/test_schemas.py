from decimal import Decimal, localcontext

import pytest
from pydantic import TypeAdapter

from app.api.schemas import Amount

AMOUNT = TypeAdapter(Amount)


def serialize(value: Decimal) -> str:
    result = AMOUNT.dump_python(value, mode="json")
    assert isinstance(result, str)
    return result


def test_serialization_keeps_every_digit_beyond_context_precision() -> None:
    with localcontext() as context:
        context.prec = 60
        value = Decimal(1) / Decimal(7) * 439
    assert len(value.as_tuple().digits) > 28  # more digits than the default context precision
    text = serialize(value)
    assert Decimal(text) == value
    assert str(value) == text


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("0", "0"),
        ("0.000", "0"),
        ("-0", "0"),
        ("100", "100"),
        ("1E+2", "100"),
        ("1200.00", "1200"),
        ("10.500", "10.5"),
        ("0.0010", "0.001"),
        ("-938.10", "-938.1"),
        ("1921.05", "1921.05"),
    ],
)
def test_trailing_zeros_stripped_only_after_decimal_point(value: str, expected: str) -> None:
    assert serialize(Decimal(value)) == expected
