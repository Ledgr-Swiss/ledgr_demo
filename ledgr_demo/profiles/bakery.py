"""Boulangerie du Lac SA profile — commerce alimentaire à Yverdon.

Profil : boulangerie-tea-room 5 employés, achats fréquents matières premières,
caisse quotidienne agrégée hebdomadairement, TVA mixte 2.6% (denrées) / 8.1%
(boissons, équipement, services).
"""
from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Any

from ledgr_demo.utils import (
    PERIOD_START,
    PERIOD_END,
    annual_dates,
    monthly_dates,
    quarterly_dates,
    randomize_amount,
    tva_amount,
    tva_breakdown,
    weekly_dates,
)


SUPPLIERS = [
    # Récurrents très fréquents (matières premières — TVA 2.6% denrées)
    {"supplier_name": "Pistor SA", "default_expense_account": "4200 - Charges de marchandises",
     "tva_rate": 2.6, "recurrence": "biweekly", "base_amount_chf": 1200.00, "variance": 0.25},
    {"supplier_name": "Boillat Frères Sàrl", "default_expense_account": "4200 - Charges de marchandises",
     "tva_rate": 2.6, "recurrence": "weekly", "base_amount_chf": 380.00, "variance": 0.20},
    {"supplier_name": "Migros Pro", "default_expense_account": "4200 - Charges de marchandises",
     "tva_rate": 2.6, "recurrence": "weekly", "base_amount_chf": 220.00, "variance": 0.30},

    # Récurrents mensuels
    {"supplier_name": "Romande Energie SA", "default_expense_account": "6400 - Charges d'énergie et évacuation des déchets",
     "tva_rate": 8.1, "recurrence": "monthly", "base_amount_chf": 800.00, "variance": 0.20},
    {"supplier_name": "Service de l'Eau Yverdon", "default_expense_account": "6400 - Charges d'énergie et évacuation des déchets",
     "tva_rate": 8.1, "recurrence": "monthly", "base_amount_chf": 120.00, "variance": 0.10},
    {"supplier_name": "Gérance Bovay SA", "default_expense_account": "6000 - Charges de locaux",
     "tva_rate": 0.0, "recurrence": "monthly", "base_amount_chf": 3200.00, "variance": 0.0},
    {"supplier_name": "Swisscom SA", "default_expense_account": "6510 - Frais de télécommunication",
     "tva_rate": 8.1, "recurrence": "monthly", "base_amount_chf": 180.00, "variance": 0.05},

    # Récurrents trimestriels
    {"supplier_name": "Caisse AVS Vaud", "default_expense_account": "5700 - Charges sociales AVS/AI/APG/AC",
     "tva_rate": 0.0, "recurrence": "quarterly", "base_amount_chf": 3000.00, "variance": 0.10},

    # Récurrents annuels
    {"supplier_name": "SUVA", "default_expense_account": "5740 - Charges sociales LAA",
     "tva_rate": 0.0, "recurrence": "annual", "base_amount_chf": 4500.00, "variance": 0.0,
     "month": 1, "day": 31},
    {"supplier_name": "Lucerne Compagnie d'Assurance", "default_expense_account": "6300 - Assurances choses, droits, taxes, autorisations",
     "tva_rate": 0.0, "recurrence": "annual", "base_amount_chf": 2200.00, "variance": 0.0,
     "month": 5, "day": 15},

    # Sporadiques
    {"supplier_name": "Tornos Bakery Equipment", "default_expense_account": "6570 - Frais d'informatique, leasing comp.",
     "tva_rate": 8.1, "recurrence": "sporadic", "base_amount_chf": 1500.00, "variance": 0.40, "occurrences": 3},
    {"supplier_name": "Rentokil Initial", "default_expense_account": "6100 - Entretien, réparations, remplacements",
     "tva_rate": 8.1, "recurrence": "sporadic", "base_amount_chf": 280.00, "variance": 0.10, "occurrences": 4},
    {"supplier_name": "Yverdon Toilettes", "default_expense_account": "6100 - Entretien, réparations, remplacements",
     "tva_rate": 8.1, "recurrence": "sporadic", "base_amount_chf": 95.00, "variance": 0.10, "occurrences": 6},
    {"supplier_name": "Coop City Yverdon", "default_expense_account": "6700 - Autres charges d'exploitation",
     "tva_rate": 8.1, "recurrence": "sporadic", "base_amount_chf": 130.00, "variance": 0.30, "occurrences": 4},
]

# Clients (B2B uniquement — la caisse POS est gérée via JE hebdo agrégés)
CUSTOMERS = [
    {"customer_name": "Hôtel des Bains Yverdon", "customer_group": "Commercial", "territory": "Switzerland"},
    {"customer_name": "Restaurant Le Lac Sàrl", "customer_group": "Commercial", "territory": "Switzerland"},
    {"customer_name": "École primaire de Cheseaux-Noréaz", "customer_group": "Commercial", "territory": "Switzerland"},
    {"customer_name": "Crèche Les Petits Loups", "customer_group": "Commercial", "territory": "Switzerland"},
    {"customer_name": "Mariage SA Events", "customer_group": "Commercial", "territory": "Switzerland"},
    {"customer_name": "Bar à Vins Le Cep", "customer_group": "Commercial", "territory": "Switzerland"},
]

# Items vendus en gros (B2B) — pas la vente POS quotidienne
ITEMS = [
    {"item_code": "BDL-PAIN-COLLECT", "item_name": "Pain — livraison collectivité",
     "item_group": "Products", "is_stock_item": 0, "stock_uom": "Kg",
     "default_income_account": "3000 - Produits résultant de ventes et de prestations de services", "tva_rate": 2.6,
     "default_unit_price": 8.50},
    {"item_code": "BDL-VIENN-COLLECT", "item_name": "Viennoiseries — assortiment",
     "item_group": "Products", "is_stock_item": 0, "stock_uom": "Unit",
     "default_income_account": "3000 - Produits résultant de ventes et de prestations de services", "tva_rate": 2.6,
     "default_unit_price": 1.80},
    {"item_code": "BDL-BUFFET", "item_name": "Buffet événement — par personne",
     "item_group": "Services", "is_stock_item": 0, "stock_uom": "Unit",
     "default_income_account": "3400 - Produits nets résultant de prestations de services", "tva_rate": 8.1,
     "default_unit_price": 35.00},
    {"item_code": "BDL-CAFE-LIVR", "item_name": "Café livré — kg",
     "item_group": "Products", "is_stock_item": 0, "stock_uom": "Kg",
     "default_income_account": "3000 - Produits résultant de ventes et de prestations de services", "tva_rate": 8.1,
     "default_unit_price": 28.00},
]


def _gen_purchase_invoices() -> list[dict[str, Any]]:
    ops: list[dict[str, Any]] = []
    for supplier in SUPPLIERS:
        rec = supplier["recurrence"]
        if rec == "monthly":
            dates = list(monthly_dates(day_of_month=15))
        elif rec == "biweekly":
            current = PERIOD_START
            dates = []
            while current <= PERIOD_END:
                dates.append(current)
                current += timedelta(days=14)
        elif rec == "weekly":
            dates = list(weekly_dates(weekday=2))
        elif rec == "quarterly":
            dates = list(quarterly_dates())
        elif rec == "annual":
            dates = list(annual_dates(supplier["month"], supplier["day"]))
        elif rec == "sporadic":
            occurrences = supplier.get("occurrences", 3)
            ords = sorted(random.sample(
                range(PERIOD_START.toordinal(), PERIOD_START.toordinal() + 365),
                occurrences
            ))
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
    """8 drafts récents pour démonstration de l'inbox."""
    ops: list[dict[str, Any]] = []
    sporadic = [s for s in SUPPLIERS if s["recurrence"] == "sporadic"]
    three_months_ago = PERIOD_START + timedelta(days=275)
    candidate = [(three_months_ago + timedelta(days=i)).toordinal() for i in range(90)]
    selected = sorted(random.sample(candidate, 8))
    for i, ord_ in enumerate(selected):
        s = sporadic[i % len(sporadic)]
        net = randomize_amount(s["base_amount_chf"], s.get("variance", 0.2))
        tva = tva_amount(net, s["tva_rate"])
        ops.append({
            "doctype": "Purchase Invoice",
            "posting_date": date.fromordinal(ord_).isoformat(),
            "supplier_name": s["supplier_name"],
            "expense_account": s["default_expense_account"],
            "tva_rate": s["tva_rate"],
            "net_amount": net,
            "tva_amount": tva,
            "grand_total": net + tva,
            "submit": False,
        })
    return ops


def _gen_sales_invoices() -> list[dict[str, Any]]:
    """B2B uniquement — chaque client 4 SI/an environ."""
    ops: list[dict[str, Any]] = []
    for customer in CUSTOMERS:
        for q_date in quarterly_dates():
            item = random.choice(ITEMS)
            qty = random.choice([10, 20, 50, 100])
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


def _gen_pos_caisse_journal_entries() -> list[dict[str, Any]]:
    """1 JE par semaine = caisse POS agrégée.

    Pattern :
    - DR 1000 Caisse : total exact des crédits (recettes semaine)
    - CR 3000 Production : net HT denrées 2.6%
    - CR 3400 Prestations de services : net HT boissons/services 8.1%
    - CR 2200 TVA due : TVA collectée mixte
    """
    ops: list[dict[str, Any]] = []
    for week_date in weekly_dates(weekday=6):  # dimanche = clôture caisse semaine
        gross_food = randomize_amount(7500.00, 0.15)
        gross_services = randomize_amount(300.00, 0.30)
        net_food, tva_food = tva_breakdown(gross_food, 2.6)
        net_serv, tva_serv = tva_breakdown(gross_services, 8.1)
        total_tva = round(tva_food + tva_serv, 2)
        # Force exact balance: total_caisse = sum of credits (avoids ±0.01 drift)
        total_caisse = round(net_food + net_serv + total_tva, 2)

        ops.append({
            "doctype": "Journal Entry",
            "posting_date": week_date.isoformat(),
            "title": f"Caisse semaine {week_date.isocalendar()[1]} {week_date.year}",
            "lines": [
                {"account": "1000 - Caisse", "debit": total_caisse, "credit": 0},
                {"account": "3000 - Produits résultant de ventes et de prestations de services", "debit": 0, "credit": net_food},
                {"account": "3400 - Produits nets résultant de prestations de services", "debit": 0, "credit": net_serv},
                {"account": "2200 - TVA due", "debit": 0, "credit": total_tva},
            ],
        })
    return ops


def _gen_payroll_journal_entries() -> list[dict[str, Any]]:
    """12 JE de paie mensuelle agrégée (5 employés boulangerie)."""
    ops: list[dict[str, Any]] = []
    for posting_date in monthly_dates(day_of_month=25):
        gross = randomize_amount(28000.00, 0.05)
        ahv = round(gross * 0.064, 2)
        lpp = round(gross * 0.075, 2)
        ahv_total = round(ahv * 2, 2)
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
    ops: list[dict[str, Any]] = []
    ops.extend(_gen_purchase_invoices())
    ops.extend(_gen_drafts())
    ops.extend(_gen_sales_invoices())
    ops.extend(_gen_pos_caisse_journal_entries())
    ops.extend(_gen_payroll_journal_entries())
    return ops
