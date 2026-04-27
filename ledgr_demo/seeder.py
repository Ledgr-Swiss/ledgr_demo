"""Main demo seeder orchestrator.

Order:
1. Wipe existing demo companies (idempotent)
2. Create Fiduciaire Demo SA (FID) — triggers Käfer/VEKA hook
3. Create Boulangerie du Lac SA (BDL) — triggers Käfer/VEKA hook
4. For each company: seed parties (suppliers, customers), items, then operations from the profile
"""
from __future__ import annotations

import random

import frappe

from ledgr_demo.wipe import run_wipe

SEED = 42  # Reproductibilité

COMPANIES = [
    {
        "name": "Fiduciaire Demo SA",
        "abbr": "FID",
        "country": "Switzerland",
        "default_currency": "CHF",
        "chart_of_accounts": "Standard",
    },
    {
        "name": "Boulangerie du Lac SA",
        "abbr": "BDL",
        "country": "Switzerland",
        "default_currency": "CHF",
        "chart_of_accounts": "Standard",
    },
]


def _create_company(spec: dict) -> str:
    """Create a Company doc — Käfer/VEKA chart auto-seeded via L1 hook."""
    if frappe.db.exists("Company", spec["name"]):
        return spec["name"]
    payload = {"doctype": "Company", "company_name": spec["name"], **spec}
    payload.pop("name", None)
    payload["company_name"] = spec["name"]
    doc = frappe.get_doc(payload)
    doc.insert(ignore_permissions=True)
    return doc.name


def run_seed() -> dict:
    """Run the full seed: wipe + recreate + populate profiles."""
    logger = frappe.logger("ledgr_demo")
    random.seed(SEED)

    logger.info("seed: wiping previous demo data")
    run_wipe()

    stats: dict = {"companies_created": [], "operations_seeded": {}}

    for spec in COMPANIES:
        name = _create_company(spec)
        stats["companies_created"].append(name)
        logger.info(f"seed: created Company {name}")

    # Profiles seeded in subsequent tasks — placeholder for now
    return stats
