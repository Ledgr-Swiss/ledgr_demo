"""Idempotent wipe of demo companies and their linked documents.

Order matters — deletes child docs (invoices, JEs, payments, accounts, parties)
before deleting the Company itself, since Frappe blocks Company deletion if linked
docs exist.
"""
from __future__ import annotations

import frappe

COMPANIES_TO_WIPE = [
    "Fiduciaire Demo SA",
    "Mandat Test SARL",
    "Boulangerie du Lac SA",
]

# Doctypes liés à une company, ordre de suppression (cascade manuelle).
# Note: "Bin" n'a pas de champ company (lié via warehouse) — omis car non utilisé en demo.
LINKED_DOCTYPES_BY_COMPANY = [
    "Payment Entry",
    "Sales Invoice",
    "Purchase Invoice",
    "Journal Entry",
    "GL Entry",
    "Stock Ledger Entry",
]

PURGE_DOCTYPES_BY_COMPANY = [
    "Salary Component Account",
    "Sales Taxes and Charges Template",
    "Purchase Taxes and Charges Template",
    "Mode of Payment Account",
    "Cost Center",
    "Warehouse",
]


def _delete_linked(doctype: str, company: str) -> int:
    """Hard delete all docs of `doctype` for a given company. Returns count."""
    names = frappe.db.get_all(
        doctype,
        filters={"company": company},
        pluck="name",
        limit_page_length=0,
    )
    for name in names:
        # Cancel before delete si nécessaire (docstatus 1)
        try:
            doc = frappe.get_doc(doctype, name)
            if hasattr(doc, "docstatus") and doc.docstatus == 1:
                doc.cancel()
            frappe.delete_doc(
                doctype,
                name,
                force=True,
                delete_permanently=True,
                ignore_permissions=True,
            )
        except Exception as exc:
            frappe.logger("ledgr_demo").warning(
                f"wipe: could not delete {doctype}/{name}: {exc}"
            )
    return len(names)


def _delete_accounts(company: str) -> int:
    """Delete all accounts for a company (after GL entries are gone)."""
    accounts = frappe.db.get_all(
        "Account",
        filters={"company": company},
        pluck="name",
        limit_page_length=0,
    )
    # Two-pass: non-groups first, groups last (children before parents)
    leaves = [
        a for a in accounts
        if not frappe.db.get_value("Account", a, "is_group")
    ]
    groups = [a for a in accounts if a not in leaves]
    deleted = 0
    for name in leaves + groups:
        try:
            frappe.delete_doc(
                "Account",
                name,
                force=True,
                ignore_permissions=True,
            )
            deleted += 1
        except Exception as exc:
            frappe.logger("ledgr_demo").warning(
                f"wipe: could not delete Account/{name}: {exc}"
            )
    return deleted


def _delete_company(company_name: str) -> bool:
    """Delete the Company doc itself."""
    if not frappe.db.exists("Company", company_name):
        return False
    try:
        frappe.delete_doc(
            "Company",
            company_name,
            force=True,
            ignore_permissions=True,
        )
        return True
    except Exception as exc:
        frappe.logger("ledgr_demo").error(
            f"wipe: could not delete Company/{company_name}: {exc}"
        )
        raise


def run_wipe(purge: bool = False) -> dict:
    """Wipe all demo companies. Returns counts per doctype.

    Args:
        purge: si True, supprime aussi les mappings (Salary Component Account, Tax Templates,
            Mode of Payment Account, Cost Center, Warehouse) AVANT la Company elle-même.
            Utile pour repartir d'un état complètement vierge après un changement de fixture.
    """
    logger = frappe.logger("ledgr_demo")
    stats: dict = {"companies_deleted": 0, "linked_deleted": {}, "accounts_deleted": 0}

    for company in COMPANIES_TO_WIPE:
        if not frappe.db.exists("Company", company):
            logger.info(f"wipe: {company} does not exist, skipping")
            continue

        logger.info(f"wipe: starting on {company} (purge={purge})")

        for doctype in LINKED_DOCTYPES_BY_COMPANY:
            count = _delete_linked(doctype, company)
            if count:
                stats["linked_deleted"].setdefault(doctype, 0)
                stats["linked_deleted"][doctype] += count

        if purge:
            for doctype in PURGE_DOCTYPES_BY_COMPANY:
                count = _delete_linked(doctype, company)
                if count:
                    stats["linked_deleted"].setdefault(doctype, 0)
                    stats["linked_deleted"][doctype] += count

        accounts_count = _delete_accounts(company)
        stats["accounts_deleted"] += accounts_count

        if _delete_company(company):
            stats["companies_deleted"] += 1

        logger.info(f"wipe: completed for {company}")

    return stats
