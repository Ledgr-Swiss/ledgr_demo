"""Fiduciaire Demo SA profile — services B2B fiduciaires.

Profil : cabinet 3 personnes (1 associé + 2 collaborateurs), Lausanne, mandats PME.
Plan comptable : Käfer/VEKA standard.
TVA : assujetti à 8.1% sur prestations de services (les services fiduciaires
sont à taux normal).
"""
from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Any

from ledgr_demo.utils import (
    PERIOD_START,
    annual_dates,
    monthly_dates,
    quarterly_dates,
    randomize_amount,
    tva_amount,
)

# Fournisseurs récurrents et sporadiques.
# default_expense_account = compte Käfer/VEKA utilisé par défaut, suffixé " - FID" à la création
SUPPLIERS = [
    # Récurrents mensuels
    {"supplier_name": "Swisscom SA", "default_expense_account": "6510 - Frais de télécommunication",
     "tva_rate": 8.1, "recurrence": "monthly", "base_amount_chf": 250.00, "variance": 0.05},
    {"supplier_name": "Romande Energie SA", "default_expense_account": "6400 - Charges d'énergie et évacuation des déchets",
     "tva_rate": 8.1, "recurrence": "monthly", "base_amount_chf": 80.00, "variance": 0.20},
    {"supplier_name": "Gérance Immo SA", "default_expense_account": "6000 - Charges de locaux",
     "tva_rate": 0.0, "recurrence": "monthly", "base_amount_chf": 2500.00, "variance": 0.0},
    {"supplier_name": "La Poste CH", "default_expense_account": "6510 - Frais de télécommunication",
     "tva_rate": 8.1, "recurrence": "monthly", "base_amount_chf": 50.00, "variance": 0.30},

    # Récurrents trimestriels
    {"supplier_name": "Bex Print Sàrl", "default_expense_account": "6570 - Frais d'informatique, leasing comp.",
     "tva_rate": 8.1, "recurrence": "quarterly", "base_amount_chf": 200.00, "variance": 0.15},
    {"supplier_name": "Caisse AVS Vaud", "default_expense_account": "5700 - Charges sociales AVS/AI/APG/AC",
     "tva_rate": 0.0, "recurrence": "quarterly", "base_amount_chf": 1800.00, "variance": 0.10},

    # Récurrents annuels
    {"supplier_name": "Swiss Life SA", "default_expense_account": "5710 - Charges sociales LPP",
     "tva_rate": 0.0, "recurrence": "annual", "base_amount_chf": 12000.00, "variance": 0.05,
     "month": 1, "day": 31},
    {"supplier_name": "Lucerne Compagnie d'Assurance", "default_expense_account": "6300 - Assurances choses, droits, taxes, autorisations",
     "tva_rate": 0.0, "recurrence": "annual", "base_amount_chf": 850.00, "variance": 0.0,
     "month": 6, "day": 15},
    {"supplier_name": "Info-Solutions Sàrl", "default_expense_account": "6570 - Frais d'informatique, leasing comp.",
     "tva_rate": 8.1, "recurrence": "annual", "base_amount_chf": 1800.00, "variance": 0.0,
     "month": 9, "day": 1},
    {"supplier_name": "Fiduciaire Suisse", "default_expense_account": "6700 - Autres charges d'exploitation",
     "tva_rate": 8.1, "recurrence": "annual", "base_amount_chf": 480.00, "variance": 0.0,
     "month": 1, "day": 15},

    # Sporadiques
    {"supplier_name": "Coop City Lausanne", "default_expense_account": "6700 - Autres charges d'exploitation",
     "tva_rate": 8.1, "recurrence": "sporadic", "base_amount_chf": 150.00, "variance": 0.40, "occurrences": 4},
    {"supplier_name": "Garage du Lac Sàrl", "default_expense_account": "6200 - Charges de véhicules et transports",
     "tva_rate": 8.1, "recurrence": "sporadic", "base_amount_chf": 850.00, "variance": 0.30, "occurrences": 3},
    {"supplier_name": "Restaurant La Pinte", "default_expense_account": "6640 - Charges de représentation et frais accessoires",
     "tva_rate": 8.1, "recurrence": "sporadic", "base_amount_chf": 180.00, "variance": 0.50, "occurrences": 6},
    {"supplier_name": "SBB CFF FFS", "default_expense_account": "6210 - Charges de transport, voyages et représentation",
     "tva_rate": 8.1, "recurrence": "sporadic", "base_amount_chf": 95.00, "variance": 0.40, "occurrences": 8},
    {"supplier_name": "Office Mondial SA", "default_expense_account": "6500 - Charges d'administration",
     "tva_rate": 8.1, "recurrence": "sporadic", "base_amount_chf": 220.00, "variance": 0.30, "occurrences": 3},
]

# Clients (mandats fiduciaires)
CUSTOMERS = [
    {"customer_name": "Boulangerie du Lac SA", "customer_group": "Commercial", "territory": "Switzerland"},
    {"customer_name": "Garage Romand SA", "customer_group": "Commercial", "territory": "Switzerland"},
    {"customer_name": "Cabinet Dentaire Dr. Müller Sàrl", "customer_group": "Commercial", "territory": "Switzerland"},
    {"customer_name": "Architectes Associés Lausanne SA", "customer_group": "Commercial", "territory": "Switzerland"},
    {"customer_name": "Maraîchers de Bex SA", "customer_group": "Commercial", "territory": "Switzerland"},
    {"customer_name": "Restaurant L'Auberge Sàrl", "customer_group": "Commercial", "territory": "Switzerland"},
    {"customer_name": "Yverdon Tech SA", "customer_group": "Commercial", "territory": "Switzerland"},
    {"customer_name": "Cabinet Avocats Dupont & Associés", "customer_group": "Commercial", "territory": "Switzerland"},
    {"customer_name": "Pharmacie de la Gare Vevey Sàrl", "customer_group": "Commercial", "territory": "Switzerland"},
    {"customer_name": "Société Coopérative La Combe", "customer_group": "Commercial", "territory": "Switzerland"},
]

# Items (services fiduciaires) — utilisés sur Sales Invoices
# default_income_account = compte Käfer/VEKA suffixé " - FID" à la création
ITEMS = [
    {"item_code": "FIDU-COMPTA-MENS", "item_name": "Tenue comptable mensuelle",
     "item_group": "Services", "is_stock_item": 0, "stock_uom": "Hour",
     "default_income_account": "3400 - Produits nets résultant de prestations de services", "tva_rate": 8.1,
     "default_unit_price": 350.00},
    {"item_code": "FIDU-TVA-DECL", "item_name": "Déclaration TVA trimestrielle",
     "item_group": "Services", "is_stock_item": 0, "stock_uom": "Unit",
     "default_income_account": "3400 - Produits nets résultant de prestations de services", "tva_rate": 8.1,
     "default_unit_price": 280.00},
    {"item_code": "FIDU-PAIE-MENS", "item_name": "Gestion de la paie mensuelle",
     "item_group": "Services", "is_stock_item": 0, "stock_uom": "Hour",
     "default_income_account": "3400 - Produits nets résultant de prestations de services", "tva_rate": 8.1,
     "default_unit_price": 180.00},
    {"item_code": "FIDU-CLOTURE", "item_name": "Bouclement annuel et états financiers",
     "item_group": "Services", "is_stock_item": 0, "stock_uom": "Unit",
     "default_income_account": "3400 - Produits nets résultant de prestations de services", "tva_rate": 8.1,
     "default_unit_price": 2500.00},
    {"item_code": "FIDU-CONSEIL", "item_name": "Conseil fiscal — heure",
     "item_group": "Services", "is_stock_item": 0, "stock_uom": "Hour",
     "default_income_account": "3400 - Produits nets résultant de prestations de services", "tva_rate": 8.1,
     "default_unit_price": 220.00},
    {"item_code": "FIDU-DECL-IMPOTS", "item_name": "Déclaration d'impôts personne morale",
     "item_group": "Services", "is_stock_item": 0, "stock_uom": "Unit",
     "default_income_account": "3400 - Produits nets résultant de prestations de services", "tva_rate": 8.1,
     "default_unit_price": 950.00},
]


def _gen_purchase_invoices() -> list[dict[str, Any]]:
    """Generate 12 months of supplier invoices (récurrents + sporadiques)."""
    ops: list[dict[str, Any]] = []

    for supplier in SUPPLIERS:
        rec = supplier["recurrence"]
        if rec == "monthly":
            dates = list(monthly_dates(day_of_month=15))
        elif rec == "quarterly":
            dates = list(quarterly_dates())
        elif rec == "annual":
            dates = list(annual_dates(supplier["month"], supplier["day"]))
        elif rec == "sporadic":
            occurrences = supplier.get("occurrences", 3)
            all_days = (PERIOD_START.toordinal(), PERIOD_START.toordinal() + 365)
            ords = sorted(random.sample(range(all_days[0], all_days[1]), occurrences))
            dates = [date.fromordinal(o) for o in ords]
        else:
            continue

        for posting_date in dates:
            net = randomize_amount(supplier["base_amount_chf"], supplier.get("variance", 0.1))
            tva = tva_amount(net, supplier["tva_rate"])
            ops.append({
                "doctype": "Purchase Invoice",
                "posting_date": posting_date.isoformat(),
                "supplier_name": supplier["supplier_name"],
                "expense_account": supplier["default_expense_account"],
                "tva_rate": supplier["tva_rate"],
                "net_amount": net,
                "tva_amount": tva,
                "grand_total": net + tva,
                "submit": True,
            })

    return ops


def _gen_drafts() -> list[dict[str, Any]]:
    """10 drafts en attente de catégorisation (inbox de la page Comptabilisation)."""
    ops: list[dict[str, Any]] = []
    sporadic_suppliers = [s for s in SUPPLIERS if s["recurrence"] == "sporadic"]
    # Choose 10 dates in the last 3 months of the period to simulate "récents"
    three_months_ago = PERIOD_START + timedelta(days=275)  # ~ end-of-period - 3 months
    candidate_days = [(three_months_ago + timedelta(days=i)).toordinal() for i in range(90)]
    selected_ords = sorted(random.sample(candidate_days, 10))
    for i, ord_ in enumerate(selected_ords):
        supplier = sporadic_suppliers[i % len(sporadic_suppliers)]
        net = randomize_amount(supplier["base_amount_chf"], supplier.get("variance", 0.2))
        tva = tva_amount(net, supplier["tva_rate"])
        ops.append({
            "doctype": "Purchase Invoice",
            "posting_date": date.fromordinal(ord_).isoformat(),
            "supplier_name": supplier["supplier_name"],
            "expense_account": supplier["default_expense_account"],
            "tva_rate": supplier["tva_rate"],
            "net_amount": net,
            "tva_amount": tva,
            "grand_total": net + tva,
            "submit": False,  # draft
        })
    return ops


def _gen_sales_invoices() -> list[dict[str, Any]]:
    """30+ Sales Invoices — services fiduciaires aux mandats clients."""
    ops: list[dict[str, Any]] = []

    for customer in CUSTOMERS:
        for q_date in list(quarterly_dates())[:3]:
            item = random.choice(ITEMS)
            qty = random.choice([1, 2, 3])
            unit_price = randomize_amount(item["default_unit_price"], 0.1)
            net = qty * unit_price
            tva = tva_amount(net, item["tva_rate"])
            ops.append({
                "doctype": "Sales Invoice",
                "posting_date": q_date.isoformat(),
                "customer_name": customer["customer_name"],
                "items": [{
                    "item_code": item["item_code"],
                    "qty": qty,
                    "rate": unit_price,
                    "income_account": item["default_income_account"],
                }],
                "tva_rate": item["tva_rate"],
                "net_amount": net,
                "tva_amount": tva,
                "grand_total": net + tva,
                "submit": True,
            })

    return ops


def _gen_payroll_journal_entries() -> list[dict[str, Any]]:
    """12 JE de paie mensuelle agrégée (3 employés FID).

    Pattern :
    - DR 5000 Charges de personnel : ~CHF 18'000 (3 employés × ~6k brut)
    - DR 5700 Charges sociales AVS : ~CHF 1'152 (6.4%)
    - DR 5710 Charges sociales LPP : ~CHF 1'440 (8%)
    - CR 1020 Banque : net versé
    - CR 2270 Passifs sociaux AVS/AC/APG : employer + employee share
    - CR 2271 Passifs sociaux LPP : employer + employee share
    """
    ops: list[dict[str, Any]] = []
    for posting_date in monthly_dates(day_of_month=25):
        gross = randomize_amount(18000.00, 0.05)
        ahv = round(gross * 0.064, 2)
        lpp = round(gross * 0.08, 2)
        ahv_total = round(ahv * 2, 2)   # employer + employee
        lpp_total = round(lpp * 2, 2)
        net_paid = round(gross - ahv - lpp, 2)

        ops.append({
            "doctype": "Journal Entry",
            "posting_date": posting_date.isoformat(),
            "title": f"Paie {posting_date.strftime('%B %Y')}",
            "lines": [
                {"account": "5000 - Salaires", "debit": gross, "credit": 0},
                {"account": "5700 - Charges sociales AVS/AI/APG/AC", "debit": ahv, "credit": 0},
                {"account": "5710 - Charges sociales LPP", "debit": lpp, "credit": 0},
                {"account": "1020 - Banque", "debit": 0, "credit": net_paid},
                {"account": "2270 - Passifs sociaux AVS/AC/APG", "debit": 0, "credit": ahv_total},
                {"account": "2271 - Passifs sociaux LPP", "debit": 0, "credit": lpp_total},
            ],
        })
    return ops


def generate_operations() -> list[dict[str, Any]]:
    """Generate the full 12-month operation set for the FID profile."""
    ops: list[dict[str, Any]] = []
    ops.extend(_gen_purchase_invoices())
    ops.extend(_gen_drafts())
    ops.extend(_gen_sales_invoices())
    ops.extend(_gen_payroll_journal_entries())
    return ops
