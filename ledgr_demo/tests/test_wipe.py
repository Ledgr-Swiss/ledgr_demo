"""Test wipe is idempotent — runs OK even if companies don't exist."""
from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from ledgr_demo.wipe import run_wipe, COMPANIES_TO_WIPE


class TestWipe(FrappeTestCase):
    def test_companies_to_wipe_constant(self):
        self.assertIn("Fiduciaire Demo SA", COMPANIES_TO_WIPE)
        self.assertIn("Mandat Test SARL", COMPANIES_TO_WIPE)
        self.assertIn("Boulangerie du Lac SA", COMPANIES_TO_WIPE)

    def test_wipe_idempotent_on_empty(self):
        # Wipe d'une company inexistante ne doit pas crasher
        run_wipe()
        # Re-wipe — toujours OK
        run_wipe()

    def test_wipe_removes_company_if_exists(self):
        # Crée une company minimale puis wipe
        if not frappe.db.exists("Company", "Fiduciaire Demo SA"):
            frappe.get_doc({
                "doctype": "Company",
                "company_name": "Fiduciaire Demo SA",
                "country": "Switzerland",
                "default_currency": "CHF",
                "abbr": "FID",
            }).insert(ignore_permissions=True)
            frappe.db.commit()

        self.assertTrue(frappe.db.exists("Company", "Fiduciaire Demo SA"))
        run_wipe()
        frappe.db.commit()
        self.assertFalse(frappe.db.exists("Company", "Fiduciaire Demo SA"))
