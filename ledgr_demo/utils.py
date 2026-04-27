"""Pure utility functions for the demo seeder.

No Frappe imports here — keep this importable in unit tests without DB.
"""
from __future__ import annotations

import datetime
import random
from collections.abc import Iterator
from decimal import ROUND_HALF_UP, Decimal

PERIOD_START = datetime.date(2025, 5, 1)
PERIOD_END = datetime.date(2026, 4, 30)


def _round2(value: float) -> float:
    """Round to 2 decimals with HALF_UP (Frappe currency convention)."""
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def tva_amount(net: float, rate_percent: float) -> float:
    """Compute TVA on a net amount. Returns 2-decimals rounded."""
    return _round2(net * rate_percent / 100.0)


def tva_breakdown(gross: float, rate_percent: float) -> tuple[float, float]:
    """Split a gross (TTC) amount into (net, tva)."""
    if rate_percent == 0:
        return _round2(gross), 0.0
    net = gross / (1 + rate_percent / 100.0)
    net_rounded = _round2(net)
    tva = _round2(gross - net_rounded)
    return net_rounded, tva


def monthly_dates(day_of_month: int = 15) -> Iterator[datetime.date]:
    """Yield one date per month between PERIOD_START and PERIOD_END."""
    year, month = PERIOD_START.year, PERIOD_START.month
    while True:
        try:
            date = datetime.date(year, month, day_of_month)
        except ValueError:
            # Day 31 sur février par ex. — clamp au dernier jour
            if month == 12:
                next_month = datetime.date(year + 1, 1, 1)
            else:
                next_month = datetime.date(year, month + 1, 1)
            date = next_month - datetime.timedelta(days=1)
        if date > PERIOD_END:
            return
        if date >= PERIOD_START:
            yield date
        if month == 12:
            year, month = year + 1, 1
        else:
            month += 1


def weekly_dates(weekday: int = 2) -> Iterator[datetime.date]:
    """Yield one date per week (specified weekday) between PERIOD_START and PERIOD_END.
    weekday: 0=Monday, 1=Tuesday, ..., 6=Sunday.
    """
    days_ahead = (weekday - PERIOD_START.weekday()) % 7
    current = PERIOD_START + datetime.timedelta(days=days_ahead)
    while current <= PERIOD_END:
        yield current
        current += datetime.timedelta(days=7)


def quarterly_dates() -> Iterator[datetime.date]:
    """Yield 4 dates corresponding to quarter ends within the period."""
    candidates = [
        datetime.date(2025, 6, 30),
        datetime.date(2025, 9, 30),
        datetime.date(2025, 12, 31),
        datetime.date(2026, 3, 31),
    ]
    for d in candidates:
        if PERIOD_START <= d <= PERIOD_END:
            yield d


def annual_dates(month: int, day: int) -> Iterator[datetime.date]:
    """Yield annual occurrences of (month, day) within the period."""
    for year in (PERIOD_START.year, PERIOD_END.year):
        try:
            d = datetime.date(year, month, day)
        except ValueError:
            continue
        if PERIOD_START <= d <= PERIOD_END:
            yield d


def randomize_amount(base: float, variance: float = 0.1) -> float:
    """Apply ±variance jitter to a base amount. Uses random.uniform — seed externally."""
    if variance == 0:
        return _round2(base)
    factor = 1 + random.uniform(-variance, variance)
    return _round2(base * factor)
