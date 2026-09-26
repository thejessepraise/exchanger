from __future__ import annotations

from decimal import Decimal

import pytest

from exchanger import CurrencyConverter
from exchanger.exceptions import (
    InvalidAmountError,
    InvalidCurrencyError,
    RateNotFoundError,
)
from exchanger.providers.base import ExchangeRateProvider


class FakeProvider(ExchangeRateProvider):
    def __init__(self, rates: dict[tuple[str, str], Decimal]) -> None:
        self._rates = rates

    def get_rate(self, from_currency: str, to_currency: str) -> Decimal:
        key = (from_currency, to_currency)
        if key not in self._rates:
            raise RateNotFoundError(from_currency, to_currency)
        return self._rates[key]


@pytest.fixture
def converter() -> CurrencyConverter:
    provider = FakeProvider({("USD", "GHS"): Decimal("15.5")})
    return CurrencyConverter(provider=provider)


def test_convert_returns_expected_amount(converter: CurrencyConverter) -> None:
    assert converter.convert(100, "USD", "GHS") == Decimal("1550.0")


def test_convert_returns_decimal_type(converter: CurrencyConverter) -> None:
    assert isinstance(converter.convert(100, "USD", "GHS"), Decimal)


def test_convert_accepts_case_insensitive_codes(converter: CurrencyConverter) -> None:
    assert converter.convert(10, "usd", "ghs") == Decimal("155.0")


def test_convert_same_currency_skips_provider(converter: CurrencyConverter) -> None:
    assert converter.convert(42, "USD", "USD") == Decimal("42")


def test_convert_zero_amount_is_valid(converter: CurrencyConverter) -> None:
    assert converter.convert(0, "USD", "GHS") == Decimal("0")


def test_convert_rejects_negative_amount(converter: CurrencyConverter) -> None:
    with pytest.raises(InvalidAmountError):
        converter.convert(-5, "USD", "GHS")


def test_convert_rejects_non_numeric_amount(converter: CurrencyConverter) -> None:
    with pytest.raises(InvalidAmountError):
        converter.convert("not-a-number", "USD", "GHS")


def test_convert_rejects_nan_amount(converter: CurrencyConverter) -> None:
    with pytest.raises(InvalidAmountError):
        converter.convert(float("nan"), "USD", "GHS")


def test_convert_rejects_invalid_currency_code(converter: CurrencyConverter) -> None:
    with pytest.raises(InvalidCurrencyError):
        converter.convert(100, "USD", "XXX")


def test_convert_propagates_rate_not_found(converter: CurrencyConverter) -> None:
    with pytest.raises(RateNotFoundError):
        converter.convert(100, "GHS", "EUR")


def test_get_exchange_rate_returns_provider_rate(converter: CurrencyConverter) -> None:
    assert converter.get_exchange_rate("USD", "GHS") == Decimal("15.5")


def test_get_exchange_rate_returns_decimal_type(converter: CurrencyConverter) -> None:
    assert isinstance(converter.get_exchange_rate("USD", "GHS"), Decimal)


def test_get_exchange_rate_same_currency_returns_one(converter: CurrencyConverter) -> None:
    assert converter.get_exchange_rate("EUR", "EUR") == Decimal("1")


def test_convert_accepts_int_input(converter: CurrencyConverter) -> None:
    assert converter.convert(100, "USD", "GHS") == Decimal("1550.0")


def test_convert_accepts_float_input(converter: CurrencyConverter) -> None:
    assert converter.convert(100.50, "USD", "GHS") == Decimal("100.5") * Decimal("15.5")


def test_convert_accepts_string_input(converter: CurrencyConverter) -> None:
    assert converter.convert("100.50", "USD", "GHS") == Decimal("100.50") * Decimal("15.5")


def test_convert_accepts_decimal_input(converter: CurrencyConverter) -> None:
    assert converter.convert(Decimal("100.50"), "USD", "GHS") == Decimal("100.50") * Decimal("15.5")


def test_convert_does_not_introduce_float_rounding_error() -> None:
    provider = FakeProvider({("USD", "GHS"): Decimal("1.1")})
    converter = CurrencyConverter(provider=provider)
    result = converter.convert("0.1", "USD", "GHS")
    assert result == Decimal("0.1") * Decimal("1.1")
    assert result != Decimal(str(0.1 * 1.1))


def test_convert_rejects_infinite_amount(converter: CurrencyConverter) -> None:
    with pytest.raises(InvalidAmountError):
        converter.convert(float("inf"), "USD", "GHS")
