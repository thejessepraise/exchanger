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
    result = converter.convert(100, "USD", "GHS")
    assert result == Decimal("1550.00")
    assert str(result) == "1550.00"


def test_convert_returns_decimal_type(converter: CurrencyConverter) -> None:
    assert isinstance(converter.convert(100, "USD", "GHS"), Decimal)


def test_convert_accepts_case_insensitive_codes(converter: CurrencyConverter) -> None:
    result = converter.convert(10, "usd", "ghs")
    assert result == Decimal("155.00")
    assert str(result) == "155.00"


def test_convert_same_currency_skips_provider(converter: CurrencyConverter) -> None:
    result = converter.convert(42, "USD", "USD")
    assert result == Decimal("42.00")
    assert str(result) == "42.00"


def test_convert_zero_amount_is_valid(converter: CurrencyConverter) -> None:
    result = converter.convert(0, "USD", "GHS")
    assert result == Decimal("0.00")
    assert str(result) == "0.00"


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
    result = converter.convert(100, "USD", "GHS")
    assert result == Decimal("1550.00")
    assert str(result) == "1550.00"


def test_convert_accepts_float_input(converter: CurrencyConverter) -> None:
    result = converter.convert(100.50, "USD", "GHS")
    assert result == Decimal("1557.75")
    assert str(result) == "1557.75"


def test_convert_accepts_string_input(converter: CurrencyConverter) -> None:
    result = converter.convert("100.50", "USD", "GHS")
    assert result == Decimal("1557.75")
    assert str(result) == "1557.75"


def test_convert_accepts_decimal_input(converter: CurrencyConverter) -> None:
    result = converter.convert(Decimal("100.50"), "USD", "GHS")
    assert result == Decimal("1557.75")
    assert str(result) == "1557.75"


def test_convert_does_not_introduce_float_rounding_error() -> None:
    provider = FakeProvider({("USD", "GHS"): Decimal("1.1")})
    converter = CurrencyConverter(provider=provider)
    result = converter.convert("0.1", "USD", "GHS")
    assert result == Decimal("0.11")
    assert str(result) == "0.11"
    assert result != Decimal(str(0.1 * 1.1))


def test_convert_rejects_infinite_amount(converter: CurrencyConverter) -> None:
    with pytest.raises(InvalidAmountError):
        converter.convert(float("inf"), "USD", "GHS")


def test_convert_quantizes_to_two_decimal_places_required_cases() -> None:
    provider = FakeProvider({("USD", "GHS"): Decimal("1")})
    converter = CurrencyConverter(provider=provider)

    res1 = converter.convert(Decimal("1500.7689"), "USD", "GHS")
    assert res1 == Decimal("1500.77")
    assert str(res1) == "1500.77"

    res2 = converter.convert(100, "USD", "GHS")
    assert res2 == Decimal("100.00")
    assert str(res2) == "100.00"

    res3 = converter.convert(25.5, "USD", "GHS")
    assert res3 == Decimal("25.50")
    assert str(res3) == "25.50"

    res4 = converter.convert(25.567, "USD", "GHS")
    assert res4 == Decimal("25.57")
    assert str(res4) == "25.57"

    res5 = converter.convert(999.9999, "USD", "GHS")
    assert res5 == Decimal("1000.00")
    assert str(res5) == "1000.00"


def test_convert_half_cent_rounding_half_up() -> None:
    provider = FakeProvider({("USD", "GHS"): Decimal("1")})
    converter = CurrencyConverter(provider=provider)

    res1 = converter.convert("2.505", "USD", "GHS")
    assert res1 == Decimal("2.51")
    assert str(res1) == "2.51"

    res2 = converter.convert("2.515", "USD", "GHS")
    assert res2 == Decimal("2.52")
    assert str(res2) == "2.52"


def test_convert_returns_decimal_and_no_float_conversion() -> None:
    provider = FakeProvider({("USD", "GHS"): Decimal("15.507689")})
    converter = CurrencyConverter(provider=provider)
    result = converter.convert(100, "USD", "GHS")
    assert isinstance(result, Decimal)
    assert not isinstance(result, float)
    assert str(result) == "1550.77"


def test_get_exchange_rate_retains_full_precision() -> None:
    provider = FakeProvider({("USD", "GHS"): Decimal("15.507689")})
    converter = CurrencyConverter(provider=provider)
    rate = converter.get_exchange_rate("USD", "GHS")
    assert rate == Decimal("15.507689")
    assert str(rate) == "15.507689"
