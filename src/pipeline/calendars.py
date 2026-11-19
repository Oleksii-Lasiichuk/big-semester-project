"""Holidays and symbolic dates in Ukraine and Russia, 2022 onwards."""
from datetime import date, timedelta

from dateutil.easter import EASTER_ORTHODOX, easter

FIXED = [
    # (month, day, name, country, first_year, last_year)
    (1, 1, "New Year", "both", 2022, None),
    (1, 7, "Orthodox Christmas", "RU", 2022, None),
    (1, 7, "Orthodox Christmas", "UA", 2022, 2023),
    (12, 25, "Christmas", "UA", 2023, None),
    (2, 23, "Defender of the Fatherland Day", "RU", 2022, None),
    (2, 24, "Anniversary of the full-scale invasion", "UA", 2023, None),
    (3, 8, "International Women's Day", "both", 2022, None),
    (5, 1, "Labour Day", "both", 2022, None),
    (5, 8, "Day of Remembrance and Victory", "UA", 2023, None),
    (5, 9, "Victory Day", "RU", 2022, None),
    (6, 12, "Russia Day", "RU", 2022, None),
    (6, 28, "Constitution Day", "UA", 2022, None),
    (8, 23, "State Flag Day", "UA", 2022, None),
    (8, 24, "Independence Day", "UA", 2022, None),
    (10, 1, "Defenders Day", "UA", 2023, None),
    (10, 14, "Defenders Day", "UA", 2022, 2022),
    (11, 4, "Unity Day", "RU", 2022, None),
    (12, 31, "New Year's Eve", "both", 2022, None),
]


def holidays(years=range(2022, 2027)):
    rows = []
    for y in years:
        for m, d, name, c, y0, y1 in FIXED:
            if y >= y0 and (y1 is None or y <= y1):
                rows.append((date(y, m, d), name, c))
        e = easter(y, EASTER_ORTHODOX)
        rows += [(e, "Orthodox Easter", "both"), (e + timedelta(days=49), "Trinity (Pentecost)", "both")]
    return sorted(rows)
