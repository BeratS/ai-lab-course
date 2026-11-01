"""Parse Albanian-language dates such as '28 tetor 2026'."""
import re
import unicodedata
from datetime import date

MONTHS = {
    "janar": 1,
    "shkurt": 2,
    "mars": 3,
    "prill": 4,
    "maj": 5,
    "qershor": 6,
    "korrik": 7,
    "gusht": 8,
    "shtator": 9,
    "tetor": 10,
    "nëntor": 11,
    "dhjetor": 12,
}

# Also accept the common ASCII spelling without the diacritic.
_ALIASES = {"nentor": 11}

_PATTERN = re.compile(r"^(\d{1,2})\s+(\S+)\s+(\d{4})$")


def parse_date(text):
    """Convert text like '28 tetor 2026' to a datetime.date.

    Case-insensitive, tolerant of extra whitespace.
    Raises ValueError (message includes the original text) for invalid input.
    """
    if not isinstance(text, str):
        raise ValueError(
            f"Invalid date {text!r}: expected a string, got {type(text).__name__}"
        )
    normalized = unicodedata.normalize("NFC", text).strip()
    match = _PATTERN.match(normalized)
    if not match:
        raise ValueError(
            f"Invalid date {text!r}: expected format 'DD month YYYY', "
            "e.g. '28 tetor 2026'"
        )
    day_s, month_s, year_s = match.groups()
    month_key = month_s.lower()
    month = MONTHS.get(month_key) or _ALIASES.get(month_key)
    if month is None:
        raise ValueError(f"Invalid date {text!r}: unknown Albanian month {month_s!r}")
    try:
        return date(int(year_s), month, int(day_s))
    except ValueError as exc:
        # e.g. day out of range for the month, or year 0
        raise ValueError(f"Invalid date {text!r}: {exc}") from None
