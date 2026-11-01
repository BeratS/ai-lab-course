from datetime import date

from albanian_dates import parse_date, MONTHS


def raises_value_error(text):
    try:
        parse_date(text)
    except ValueError:
        return True
    return False


assert parse_date("28 tetor 2026") == date(2026, 10, 28)
assert parse_date("1 Janar 2026") == date(2026, 1, 1)
assert parse_date("15  nëntor 2025") == date(2025, 11, 15)
assert parse_date("  5 DHJETOR 2024  ") == date(2024, 12, 5)
assert parse_date("10 NËNTOR 2020") == date(2020, 11, 10)
assert parse_date("29 shkurt 2024") == date(2024, 2, 29)  # leap year

# All 12 months
names = ["janar", "shkurt", "mars", "prill", "maj", "qershor",
         "korrik", "gusht", "shtator", "tetor", "nëntor", "dhjetor"]
assert len(MONTHS) == 12
for i, name in enumerate(names, start=1):
    assert parse_date(f"3 {name} 2023") == date(2023, i, 3)
    assert parse_date(f"3 {name.upper()} 2023") == date(2023, i, 3)
    assert parse_date(f"3 {name.capitalize()} 2023") == date(2023, i, 3)

# Invalid input
assert raises_value_error("32 tetor 2026")
assert raises_value_error("5 xyz 2026")
assert raises_value_error("29 shkurt 2025")  # not a leap year
assert raises_value_error("0 mars 2025")
assert raises_value_error("")
assert raises_value_error("tetor 2026")
assert raises_value_error("28 tetor")
assert raises_value_error(None)


def test_error_message_includes_original_text():
    for bad in ["32 tetor 2026", "5 xyz 2026", "29 shkurt 2025",
                "tetor 2026", "  0 mars 2025 "]:
        try:
            parse_date(bad)
        except ValueError as exc:
            assert repr(bad) in str(exc), str(exc)
            assert "Invalid date" in str(exc), str(exc)
        else:
            raise AssertionError(f"no ValueError for {bad!r}")


test_error_message_includes_original_text()

print("ALL TESTS PASSED")
