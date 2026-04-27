"""Pure unit tests for ledgr_demo utilities (no DB)."""
import datetime
from frappe.tests.utils import FrappeTestCase

from ledgr_demo.utils import (
    tva_amount,
    tva_breakdown,
    monthly_dates,
    weekly_dates,
    quarterly_dates,
    annual_dates,
    randomize_amount,
    PERIOD_START,
    PERIOD_END,
)


class TestTVAHelpers(FrappeTestCase):
    def test_tva_amount_standard(self):
        # 100 CHF HT à 8.1% → 8.10 CHF de TVA
        self.assertEqual(tva_amount(100.00, 8.1), 8.10)

    def test_tva_amount_food(self):
        # 100 CHF HT à 2.6% → 2.60 CHF de TVA
        self.assertEqual(tva_amount(100.00, 2.6), 2.60)

    def test_tva_amount_rounded_chf(self):
        # 99.95 CHF HT à 8.1% = 8.09595 → 8.10 (arrondi à 2 décimales, pas 0.05)
        self.assertEqual(tva_amount(99.95, 8.1), 8.10)

    def test_tva_amount_zero_rate(self):
        # 100 CHF à 0% (exonéré) → 0
        self.assertEqual(tva_amount(100.00, 0.0), 0.00)

    def test_tva_breakdown_simple(self):
        # 108.10 TTC à 8.1% → HT=100.00, TVA=8.10
        ht, tva = tva_breakdown(108.10, 8.1)
        self.assertEqual(ht, 100.00)
        self.assertEqual(tva, 8.10)

    def test_tva_breakdown_food(self):
        # 102.60 TTC à 2.6% → HT=100.00, TVA=2.60
        ht, tva = tva_breakdown(102.60, 2.6)
        self.assertEqual(ht, 100.00)
        self.assertEqual(tva, 2.60)


class TestDateGenerators(FrappeTestCase):
    def test_period_constants(self):
        self.assertEqual(PERIOD_START, datetime.date(2025, 5, 1))
        self.assertEqual(PERIOD_END, datetime.date(2026, 4, 30))

    def test_monthly_dates_count(self):
        # 12 mois entre 2025-05 et 2026-04
        dates = list(monthly_dates(day_of_month=15))
        self.assertEqual(len(dates), 12)

    def test_monthly_dates_first(self):
        dates = list(monthly_dates(day_of_month=15))
        self.assertEqual(dates[0], datetime.date(2025, 5, 15))
        self.assertEqual(dates[11], datetime.date(2026, 4, 15))

    def test_weekly_dates_count(self):
        # ~52 semaines sur 12 mois
        dates = list(weekly_dates(weekday=2))  # Wednesday
        self.assertGreaterEqual(len(dates), 50)
        self.assertLessEqual(len(dates), 53)

    def test_quarterly_dates(self):
        dates = list(quarterly_dates())
        self.assertEqual(len(dates), 4)

    def test_annual_dates_single(self):
        dates = list(annual_dates(month=11, day=30))
        self.assertEqual(len(dates), 1)
        self.assertEqual(dates[0], datetime.date(2025, 11, 30))

    def test_annual_dates_boundary_filters_pre_period(self):
        # 2025-04-15 is before PERIOD_START (2025-05-01) → filtered out.
        # 2026-04-15 is within the period → yielded.
        dates = list(annual_dates(month=4, day=15))
        self.assertEqual(len(dates), 1)
        self.assertEqual(dates[0], datetime.date(2026, 4, 15))


class TestRandomize(FrappeTestCase):
    def test_randomize_amount_within_bounds(self):
        # base=100, variance=0.1 → entre 90 et 110
        for _ in range(20):
            v = randomize_amount(100, variance=0.1)
            self.assertGreaterEqual(v, 90.0)
            self.assertLessEqual(v, 110.0)

    def test_randomize_amount_deterministic_with_seed(self):
        import random
        random.seed(42)
        v1 = randomize_amount(100, variance=0.1)
        random.seed(42)
        v2 = randomize_amount(100, variance=0.1)
        self.assertEqual(v1, v2)

    def test_randomize_amount_zero_variance(self):
        self.assertEqual(randomize_amount(100, variance=0.0), 100.00)
