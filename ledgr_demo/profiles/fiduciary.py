"""Fiduciaire Demo SA profile — services B2B fiduciaires.

Profil : cabinet 3 personnes (1 associé + 2 collaborateurs), Lausanne, mandats PME.
Plan comptable : Käfer/VEKA standard.
TVA : assujetti à 8.1% sur prestations de services (les services fiduciaires
sont à taux normal).
"""
from __future__ import annotations

# Fournisseurs récurrents et sporadiques.
# default_expense_account = compte Käfer/VEKA utilisé par défaut, suffixé " - FID" à la création
SUPPLIERS = [
    # Récurrents mensuels
    {"supplier_name": "Swisscom SA", "default_expense_account": "6510 - Frais de télécommunication",
     "tva_rate": 8.1, "recurrence": "monthly", "base_amount_chf": 250.00, "variance": 0.05},
    {"supplier_name": "Romande Energie SA", "default_expense_account": "6500 - Énergie de production",
     "tva_rate": 8.1, "recurrence": "monthly", "base_amount_chf": 80.00, "variance": 0.20},
    {"supplier_name": "Gérance Immo SA", "default_expense_account": "6000 - Charges de locaux",
     "tva_rate": 0.0, "recurrence": "monthly", "base_amount_chf": 2500.00, "variance": 0.0},
    {"supplier_name": "La Poste CH", "default_expense_account": "6500 - Énergie de production",
     "tva_rate": 8.1, "recurrence": "monthly", "base_amount_chf": 50.00, "variance": 0.30},

    # Récurrents trimestriels
    {"supplier_name": "Bex Print Sàrl", "default_expense_account": "6570 - Frais d'informatique, leasing comp.",
     "tva_rate": 8.1, "recurrence": "quarterly", "base_amount_chf": 200.00, "variance": 0.15},
    {"supplier_name": "Caisse AVS Vaud", "default_expense_account": "5700 - Charges sociales AVS/AC/APG",
     "tva_rate": 0.0, "recurrence": "quarterly", "base_amount_chf": 1800.00, "variance": 0.10},

    # Récurrents annuels
    {"supplier_name": "Swiss Life SA", "default_expense_account": "5710 - Charges sociales LPP",
     "tva_rate": 0.0, "recurrence": "annual", "base_amount_chf": 12000.00, "variance": 0.05,
     "month": 1, "day": 31},
    {"supplier_name": "Lucerne Compagnie d'Assurance", "default_expense_account": "6300 - Assurance choses",
     "tva_rate": 0.0, "recurrence": "annual", "base_amount_chf": 850.00, "variance": 0.0,
     "month": 6, "day": 15},
    {"supplier_name": "Info-Solutions Sàrl", "default_expense_account": "6570 - Frais d'informatique, leasing comp.",
     "tva_rate": 8.1, "recurrence": "annual", "base_amount_chf": 1800.00, "variance": 0.0,
     "month": 9, "day": 1},
    {"supplier_name": "Fiduciaire Suisse", "default_expense_account": "6800 - Cotisations associatives",
     "tva_rate": 8.1, "recurrence": "annual", "base_amount_chf": 480.00, "variance": 0.0,
     "month": 1, "day": 15},

    # Sporadiques (déclenchés au hasard 1-3x sur la période)
    {"supplier_name": "Coop City Lausanne", "default_expense_account": "6500 - Énergie de production",
     "tva_rate": 8.1, "recurrence": "sporadic", "base_amount_chf": 150.00, "variance": 0.40, "occurrences": 4},
    {"supplier_name": "Garage du Lac Sàrl", "default_expense_account": "6200 - Entretien et réparation véhicules",
     "tva_rate": 8.1, "recurrence": "sporadic", "base_amount_chf": 850.00, "variance": 0.30, "occurrences": 3},
    {"supplier_name": "Restaurant La Pinte", "default_expense_account": "6640 - Charges de représentation et frais accessoires",
     "tva_rate": 8.1, "recurrence": "sporadic", "base_amount_chf": 180.00, "variance": 0.50, "occurrences": 6},
    {"supplier_name": "SBB CFF FFS", "default_expense_account": "6210 - Charges de transport, voyages et représent.",
     "tva_rate": 8.1, "recurrence": "sporadic", "base_amount_chf": 95.00, "variance": 0.40, "occurrences": 8},
    {"supplier_name": "Office Mondial SA", "default_expense_account": "6500 - Énergie de production",
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
     "default_income_account": "3400 - Prestations de services", "tva_rate": 8.1,
     "default_unit_price": 350.00},
    {"item_code": "FIDU-TVA-DECL", "item_name": "Déclaration TVA trimestrielle",
     "item_group": "Services", "is_stock_item": 0, "stock_uom": "Unit",
     "default_income_account": "3400 - Prestations de services", "tva_rate": 8.1,
     "default_unit_price": 280.00},
    {"item_code": "FIDU-PAIE-MENS", "item_name": "Gestion de la paie mensuelle",
     "item_group": "Services", "is_stock_item": 0, "stock_uom": "Hour",
     "default_income_account": "3400 - Prestations de services", "tva_rate": 8.1,
     "default_unit_price": 180.00},
    {"item_code": "FIDU-CLOTURE", "item_name": "Bouclement annuel et états financiers",
     "item_group": "Services", "is_stock_item": 0, "stock_uom": "Unit",
     "default_income_account": "3400 - Prestations de services", "tva_rate": 8.1,
     "default_unit_price": 2500.00},
    {"item_code": "FIDU-CONSEIL", "item_name": "Conseil fiscal — heure",
     "item_group": "Services", "is_stock_item": 0, "stock_uom": "Hour",
     "default_income_account": "3400 - Prestations de services", "tva_rate": 8.1,
     "default_unit_price": 220.00},
    {"item_code": "FIDU-DECL-IMPOTS", "item_name": "Déclaration d'impôts personne morale",
     "item_group": "Services", "is_stock_item": 0, "stock_uom": "Unit",
     "default_income_account": "3400 - Prestations de services", "tva_rate": 8.1,
     "default_unit_price": 950.00},
]
