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


class TestFidOperationsGenerator(FrappeTestCase):
    def test_returns_list_of_operations(self):
        from ledgr_demo.profiles.fiduciary import generate_operations
        ops = generate_operations()
        self.assertIsInstance(ops, list)

    def test_purchase_invoices_volume(self):
        # Au moins 60 PI (récurrentes mensuelles + trimestrielles + annuelles + sporadiques)
        from ledgr_demo.profiles.fiduciary import generate_operations
        ops = generate_operations()
        pi = [o for o in ops if o["doctype"] == "Purchase Invoice"]
        self.assertGreaterEqual(len(pi), 60)
        self.assertLessEqual(len(pi), 120)

    def test_drafts_count(self):
        # ~10 drafts en attente de catégorisation (inbox)
        from ledgr_demo.profiles.fiduciary import generate_operations
        ops = generate_operations()
        drafts = [o for o in ops if o["doctype"] == "Purchase Invoice" and o.get("submit") is False]
        self.assertGreaterEqual(len(drafts), 8)
        self.assertLessEqual(len(drafts), 15)

    def test_sales_invoices_volume(self):
        from ledgr_demo.profiles.fiduciary import generate_operations
        ops = generate_operations()
        si = [o for o in ops if o["doctype"] == "Sales Invoice"]
        self.assertGreaterEqual(len(si), 25)

    def test_journal_entries_monthly_payroll(self):
        # 12 JE de paie mensuelle
        from ledgr_demo.profiles.fiduciary import generate_operations
        ops = generate_operations()
        je = [o for o in ops if o["doctype"] == "Journal Entry"]
        self.assertEqual(len(je), 12)

    def test_each_operation_has_required_fields(self):
        from ledgr_demo.profiles.fiduciary import generate_operations
        ops = generate_operations()
        for op in ops:
            self.assertIn("doctype", op)
            self.assertIn("posting_date", op)
            self.assertIn(op["doctype"], ("Purchase Invoice", "Sales Invoice", "Journal Entry"))

    def test_journal_entries_balanced(self):
        # Double-entrée : sum debits == sum credits par JE
        from ledgr_demo.profiles.fiduciary import generate_operations
        ops = generate_operations()
        je_ops = [o for o in ops if o["doctype"] == "Journal Entry"]
        for je in je_ops:
            total_debit = sum(line.get("debit", 0) for line in je["lines"])
            total_credit = sum(line.get("credit", 0) for line in je["lines"])
            self.assertAlmostEqual(total_debit, total_credit, places=2)

    def test_purchase_invoices_have_tva_field(self):
        from ledgr_demo.profiles.fiduciary import generate_operations
        ops = generate_operations()
        pi_ops = [o for o in ops if o["doctype"] == "Purchase Invoice"]
        for pi in pi_ops:
            self.assertIn("tva_rate", pi)
            self.assertIn("net_amount", pi)


class TestBdlProfileData(FrappeTestCase):
    def test_suppliers_minimum_count(self):
        from ledgr_demo.profiles.bakery import SUPPLIERS as BDL_SUPPLIERS
        self.assertGreaterEqual(len(BDL_SUPPLIERS), 12)

    def test_suppliers_required_food(self):
        from ledgr_demo.profiles.bakery import SUPPLIERS as BDL_SUPPLIERS
        names = [s["supplier_name"] for s in BDL_SUPPLIERS]
        for required in ["Pistor SA", "Migros Pro", "Boillat Frères Sàrl"]:
            self.assertIn(required, names)

    def test_suppliers_have_mixed_tva(self):
        from ledgr_demo.profiles.bakery import SUPPLIERS as BDL_SUPPLIERS
        rates = {s["tva_rate"] for s in BDL_SUPPLIERS}
        self.assertIn(2.6, rates)
        self.assertIn(8.1, rates)

    def test_items_for_pos_caisse(self):
        from ledgr_demo.profiles.bakery import ITEMS as BDL_ITEMS
        rates = {i["tva_rate"] for i in BDL_ITEMS}
        self.assertIn(2.6, rates)
        self.assertIn(8.1, rates)


class TestBdlOperationsGenerator(FrappeTestCase):
    def test_returns_list(self):
        from ledgr_demo.profiles.bakery import generate_operations
        self.assertIsInstance(generate_operations(), list)

    def test_purchase_invoices_high_volume(self):
        from ledgr_demo.profiles.bakery import generate_operations
        ops = generate_operations()
        pi = [o for o in ops if o["doctype"] == "Purchase Invoice"]
        self.assertGreaterEqual(len(pi), 80)

    def test_journal_entries_pos_caisse(self):
        from ledgr_demo.profiles.bakery import generate_operations
        ops = generate_operations()
        je = [o for o in ops if o["doctype"] == "Journal Entry"]
        self.assertGreaterEqual(len(je), 50)

    def test_drafts_present(self):
        from ledgr_demo.profiles.bakery import generate_operations
        ops = generate_operations()
        drafts = [o for o in ops if o["doctype"] == "Purchase Invoice" and o.get("submit") is False]
        self.assertGreaterEqual(len(drafts), 5)
