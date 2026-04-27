"""Tests for profile data generators (counts, structure, TVA balance)."""
from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from ledgr_demo.profiles.fiduciary import (
    SUPPLIERS as FID_SUPPLIERS,
    CUSTOMERS as FID_CUSTOMERS,
    ITEMS as FID_ITEMS,
)


class TestFidProfileData(FrappeTestCase):
    def test_suppliers_minimum_count(self):
        # Au moins 15 fournisseurs réalistes pour un cabinet fiduciaire
        self.assertGreaterEqual(len(FID_SUPPLIERS), 15)

    def test_suppliers_required_recurring(self):
        # Récurrents critiques pour la démonstration de l'agent IA
        names = [s["supplier_name"] for s in FID_SUPPLIERS]
        for required in ["Swisscom SA", "Romande Energie SA", "Gérance Immo SA",
                         "La Poste CH", "Swiss Life SA"]:
            self.assertIn(required, names, f"Missing required supplier: {required}")

    def test_each_supplier_has_default_account(self):
        # Pour permettre à l'agent de catégorisation de proposer
        for s in FID_SUPPLIERS:
            self.assertIn("default_expense_account", s,
                          f"{s['supplier_name']} missing default_expense_account")

    def test_customers_minimum_count(self):
        self.assertGreaterEqual(len(FID_CUSTOMERS), 8)

    def test_items_minimum_count(self):
        # Au moins un item par catégorie de prestation fiduciaire
        self.assertGreaterEqual(len(FID_ITEMS), 5)

    def test_items_required_fields(self):
        for item in FID_ITEMS:
            self.assertIn("item_code", item)
            self.assertIn("item_name", item)
            self.assertIn("default_income_account", item)
