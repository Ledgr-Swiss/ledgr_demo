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
# Ordre :
# 1. Documents transactionnels — vidés en premier pour libérer GL Entries
# 2. Mappings qui réfèrent les comptes — vidés AVANT _delete_accounts, sinon
#    Frappe.delete_doc("Account") échoue silencieusement à cause des FK et
#    laisse des comptes orphelins qui bloquent le re-seed suivant.
LINKED_DOCTYPES_BY_COMPANY = [
    "Payment Entry",
    "Sales Invoice",
    "Purchase Invoice",
    "Journal Entry",
    "GL Entry",
    "Stock Ledger Entry",
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


def run_wipe() -> dict:
    """Wipe all demo companies and their linked records. Returns counts per doctype.

    Toujours thorough : supprime mappings (Tax Templates, Salary Component Account,
    Mode of Payment Account, Cost Center, Warehouse) avant les comptes, pour éviter
    les comptes orphelins qui bloquent le re-seed suivant.

    Robuste contre les orphelins : process une Company même si son doc Frappe a
    déjà été supprimé tant que des Accounts/GL Entries traînent encore. Fallback
    SQL DELETE pour GL Entry et Account quand la cascade Frappe laisse des résidus
    (ERPNext.Account.on_trash refuse la suppression d'un compte avec GL Entries
    cancellées même via delete_doc force=True).
    """
    logger = frappe.logger("ledgr_demo")
    stats: dict = {"companies_deleted": 0, "linked_deleted": {}, "accounts_deleted": 0}

    for company in COMPANIES_TO_WIPE:
        company_exists = bool(frappe.db.exists("Company", company))
        has_orphans = bool(
            frappe.db.exists("Account", {"company": company})
            or frappe.db.exists("GL Entry", {"company": company})
        )
        if not company_exists and not has_orphans:
            logger.info(f"wipe: {company} absent + no orphans, skipping")
            continue

        logger.info(f"wipe: cleaning {company} (exists={company_exists}, orphans={has_orphans})")

        for doctype in LINKED_DOCTYPES_BY_COMPANY:
            count = _delete_linked(doctype, company)
            if count:
                stats["linked_deleted"].setdefault(doctype, 0)
                stats["linked_deleted"][doctype] += count

        # SQL fallback : delete_doc("GL Entry") laisse parfois les entries cancellées
        # (docstatus=2). Force-delete via SQL pour libérer les comptes ensuite.
        residue_gl = frappe.db.sql(
            "SELECT COUNT(*) FROM `tabGL Entry` WHERE company = %s", (company,)
        )[0][0]
        if residue_gl:
            frappe.db.sql("DELETE FROM `tabGL Entry` WHERE company = %s", (company,))
            logger.info(f"wipe: SQL-deleted {residue_gl} residual GL Entries for {company}")
            stats["linked_deleted"].setdefault("GL Entry", 0)
            stats["linked_deleted"]["GL Entry"] += residue_gl

        accounts_count = _delete_accounts(company)
        stats["accounts_deleted"] += accounts_count

        # SQL fallback : Account.on_trash peut encore refuser après le retrait des
        # GL Entries (e.g. tabBudget Account qui ref un compte). Cleanup final.
        residue_acc = frappe.db.sql_list(
            "SELECT name FROM `tabAccount` WHERE company = %s", (company,)
        )
        if residue_acc:
            frappe.db.sql("DELETE FROM `tabAccount` WHERE company = %s", (company,))
            logger.info(
                f"wipe: SQL-deleted {len(residue_acc)} residual Accounts for {company}: {residue_acc}"
            )
            stats["accounts_deleted"] += len(residue_acc)

        if company_exists and _delete_company(company):
            stats["companies_deleted"] += 1

        logger.info(f"wipe: completed for {company}")

    return stats
