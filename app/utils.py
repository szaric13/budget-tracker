from calendar import monthrange
from datetime import date
from decimal import Decimal, ROUND_HALF_UP


def month_bounds(month: str) -> tuple[date, date]:
    """'2026-10' -> (date(2026,10,1), date(2026,10,31))"""
    year, mon = map(int, month.split("-"))
    first = date(year, mon, 1)
    last = date(year, mon, monthrange(year, mon)[1])
    return first, last


def to_money(value) -> Decimal:
    if value is None:
        return Decimal("0.00")
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
