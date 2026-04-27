"""Integration tests — full seed creates expected counts in DB."""
from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from ledgr_demo.seeder import run_seed


class TestSeederFullRun(FrappeTestCase):
    """Seed runs end-to-end and DB has expected counts."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        run_seed()
        frappe.db.commit()

    def test_companies_created(self):
        self.assertTrue(frappe.db.exists("Company", "Fiduciaire Demo SA"))
        self.assertTrue(frappe.db.exists("Company", "Boulangerie du Lac SA"))

    def test_fid_chart_kaefer_veka_seeded(self):
        # account_number 1000 = Caisse (Käfer/VEKA)
        accounts = frappe.db.get_all(
            "Account",
            filters={"company": "Fiduciaire Demo SA", "account_number": "1000"},
            pluck="name",
        )
        self.assertEqual(len(accounts), 1)

    def test_fid_purchase_invoices_count(self):
        count = frappe.db.count("Purchase Invoice", {"company": "Fiduciaire Demo SA"})
        self.assertGreaterEqual(count, 60)

    def test_fid_sales_invoices_count(self):
        count = frappe.db.count("Sales Invoice", {"company": "Fiduciaire Demo SA"})
        self.assertGreaterEqual(count, 20)

    def test_fid_journal_entries_count(self):
        count = frappe.db.count("Journal Entry", {"company": "Fiduciaire Demo SA"})
        self.assertEqual(count, 12)

    def test_fid_gl_entries_balanced(self):
        # Sum of all debits = sum of all credits for FID
        result = frappe.db.sql(
            """SELECT COALESCE(SUM(debit), 0) as d, COALESCE(SUM(credit), 0) as c
               FROM `tabGL Entry`
               WHERE company = %s AND is_cancelled = 0""",
            ("Fiduciaire Demo SA",),
            as_dict=True,
        )
        d = float(result[0]["d"])
        c = float(result[0]["c"])
        self.assertAlmostEqual(d, c, places=2,
                               msg=f"GL imbalanced: debits={d} credits={c}")

    def test_fid_drafts_present(self):
        # ~10 drafts en attente de catégorisation
        count = frappe.db.count("Purchase Invoice", {
            "company": "Fiduciaire Demo SA",
            "docstatus": 0,
        })
        self.assertGreaterEqual(count, 5)
        self.assertLessEqual(count, 15)


class TestSeederBdl(FrappeTestCase):
    """BDL profile produces expected counts."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Each test class gets its own DB context — reseed to ensure BDL data is present.
        run_seed()
        frappe.db.commit()

    def test_bdl_company_exists(self):
        self.assertTrue(frappe.db.exists("Company", "Boulangerie du Lac SA"))

    def test_bdl_purchase_invoices(self):
        count = frappe.db.count("Purchase Invoice", {"company": "Boulangerie du Lac SA"})
        self.assertGreaterEqual(count, 80)

    def test_bdl_journal_entries_pos_plus_payroll(self):
        count = frappe.db.count("Journal Entry", {"company": "Boulangerie du Lac SA"})
        self.assertGreaterEqual(count, 50)

    def test_bdl_gl_balanced(self):
        result = frappe.db.sql(
            """SELECT COALESCE(SUM(debit), 0) as d, COALESCE(SUM(credit), 0) as c
               FROM `tabGL Entry` WHERE company = %s AND is_cancelled = 0""",
            ("Boulangerie du Lac SA",), as_dict=True,
        )
        self.assertAlmostEqual(float(result[0]["d"]), float(result[0]["c"]), places=2)
