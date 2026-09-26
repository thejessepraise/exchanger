from exchanger import CurrencyConverter

converter = CurrencyConverter()

result = converter.convert(500, "USD", "GHS")
print(result)