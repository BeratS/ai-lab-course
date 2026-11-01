import unittest
from datetime import date

from albanian_dates import parse_albanian_date


class TestAlbanianDates(unittest.TestCase):
    def test_full_month(self):
        self.assertEqual(parse_albanian_date("28 tetor 2026"), date(2026, 10, 28))

    def test_diacritics(self):
        self.assertEqual(parse_albanian_date("15 nëntor 2025"), date(2025, 11, 15))

    def test_uppercase(self):
        self.assertEqual(parse_albanian_date("1 Janar 2024"), date(2024, 1, 1))

    def test_abbreviation(self):
        self.assertEqual(parse_albanian_date("28 tet 2026"), date(2026, 10, 28))

    def test_dotted(self):
        self.assertEqual(parse_albanian_date("28.10.2026"), date(2026, 10, 28))

    def test_invalid(self):
        with self.assertRaises(ValueError):
            parse_albanian_date("32 tetor 2026")


if __name__ == "__main__":
    unittest.main(verbosity=2)
