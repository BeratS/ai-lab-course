import re
from datetime import date

MONTHS = {
    "janar": 1, "shkurt": 2, "mars": 3, "prill": 4, "maj": 5, "qershor": 6,
    "korrik": 7, "gusht": 8, "shtator": 9, "tetor": 10, "nentor": 11, "dhjetor": 12,
}


def _normalize(word):
    return word.strip().lower().replace("ë", "e").replace("ç", "c").rstrip(".")


def _lookup_month(name):
    name = _normalize(name)
    if name in MONTHS:
        return MONTHS[name]
    if len(name) >= 3:
        matches = {n for n in MONTHS if n.startswith(name)}
        if len(matches) == 1:
            return MONTHS[matches.pop()]
    raise ValueError(f"Unknown month: {name!r}")


def parse_albanian_date(text):
    """Parse '28 tetor 2026', '28 tet 2026' or '28.10.2026' into a date."""
    text = text.strip()
    if re.fullmatch(r"\d{1,2}\.\d{1,2}\.\d{4}", text):
        day, month, year = text.split(".")
    else:
        parts = text.split()
        if len(parts) != 3:
            raise ValueError(f"Invalid date: {text!r}")
        day, month_name, year = parts
        month = _lookup_month(month_name)
    return date(int(year), int(month), int(day))
