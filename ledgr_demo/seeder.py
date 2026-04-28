"""Main demo seeder orchestrator."""
from __future__ import annotations

import random
from typing import Any

import frappe

from ledgr_demo.wipe import run_wipe

SEED = 42

COMPANIES = [
    {"name": "Fiduciaire Demo SA", "abbr": "FID", "country": "Switzerland",
     "default_currency": "CHF", "chart_of_accounts": "Standard"},
    {"name": "Boulangerie du Lac SA", "abbr": "BDL", "country": "Switzerland",
     "default_currency": "CHF", "chart_of_accounts": "Standard"},
]

# Käfer/VEKA chart does not have all sub-accounts referenced in the profile.
# This remap redirects missing account numbers to the nearest parent account.
_ACCOUNT_NUMBER_REMAP: dict[str, str] = {
    "6510": "6500",  # Frais de télécommunication -> Charges d'administration et d'informatique
    "6570": "6500",  # Frais d'informatique -> Charges d'administration et d'informatique
    "6640": "6700",  # Charges de représentation -> Autres charges d'exploitation
    "6210": "6200",  # Charges de transport spécifiques -> Charges de véhicules et transports
    # BDL profile remaps
    "5740": "5720",  # Charges sociales LAA (BDL label) -> Charges sociales LAA (Käfer/VEKA 5720)
}


def _create_company(spec: dict) -> str:
    if frappe.db.exists("Company", spec["name"]):
        return spec["name"]

    # Clean up any orphaned accounts left by a partial previous wipe.
    # This can happen if wipe failed to delete group accounts that had
    # children, but the company record itself was deleted.
    orphaned = frappe.db.sql(
        "SELECT COUNT(*) as n FROM `tabAccount` WHERE company=%s",
        (spec["name"],),
        as_dict=True,
    )[0]["n"]
    if orphaned:
        frappe.db.sql("DELETE FROM `tabAccount` WHERE company=%s", (spec["name"],))
        frappe.logger("ledgr_demo").warning(
            f"seed: deleted {orphaned} orphaned Account records for {spec['name']}"
        )

    payload = {"doctype": "Company", "company_name": spec["name"], **spec}
    payload.pop("name", None)
    payload["company_name"] = spec["name"]
    doc = frappe.get_doc(payload)
    doc.insert(ignore_permissions=True)
    return doc.name


def _configure_company(company_name: str) -> None:
    """Set company defaults needed for PI/SI/JE materialization.

    ERPNext requires:
    - enable_perpetual_inventory = 0 (avoid stock_received_but_not_billed lookup)
    - default_payable_account (Payable account for creditors)
    - default_receivable_account (Receivable account for debtors)
    - round_off_account (needed for GL rounding on submit)
    - round_off_cost_center (needed alongside round_off_account)
    """
    doc = frappe.get_doc("Company", company_name)
    changed = False

    if doc.enable_perpetual_inventory:
        doc.enable_perpetual_inventory = 0
        changed = True

    if not doc.default_payable_account:
        payable = frappe.db.get_all(
            "Account",
            filters={"company": company_name, "account_number": "2000"},
            pluck="name",
            limit_page_length=1,
        )
        if payable:
            doc.default_payable_account = payable[0]
            changed = True

    if not doc.default_receivable_account:
        receivable = frappe.db.get_all(
            "Account",
            filters={"company": company_name, "account_number": "1100"},
            pluck="name",
            limit_page_length=1,
        )
        if receivable:
            doc.default_receivable_account = receivable[0]
            changed = True

    if not doc.round_off_account:
        # Use 6700 (Autres charges d'exploitation) as round-off account
        round_off = frappe.db.get_all(
            "Account",
            filters={"company": company_name, "account_number": "6700"},
            pluck="name",
            limit_page_length=1,
        )
        if round_off:
            doc.round_off_account = round_off[0]
            changed = True

    # Resolve the main (non-group) cost center for this company
    cost_center = frappe.db.get_all(
        "Cost Center",
        filters={"company": company_name, "is_group": 0},
        pluck="name",
        limit_page_length=1,
    )
    main_cc = cost_center[0] if cost_center else None

    if not doc.round_off_cost_center and main_cc:
        doc.round_off_cost_center = main_cc
        changed = True

    if not doc.cost_center and main_cc:
        doc.cost_center = main_cc
        changed = True

    if changed:
        doc.save(ignore_permissions=True)

    # Store cost center on Company record for later lookup in materializers
    frappe.local._ledgr_cc = getattr(frappe.local, "_ledgr_cc", {})
    frappe.local._ledgr_cc[company_name] = main_cc


def _ensure_group_fixtures() -> None:
    """Create missing tree fixtures that ERPNext did not seed by default.

    This instance has Supplier Groups seeded but is missing Customer Groups,
    Item Groups, Territories, UOMs, and Party Types. We create the minimum
    needed for FID.
    """
    # Party Types — required by ERPNext accounts/party.py to resolve account_type.
    # Normally created by the setup wizard; missing here since we bypassed it.
    if not frappe.db.exists("Party Type", "Customer"):
        frappe.get_doc({
            "doctype": "Party Type",
            "party_type": "Customer",
            "account_type": "Receivable",
        }).insert(ignore_permissions=True)
    if not frappe.db.exists("Party Type", "Supplier"):
        frappe.get_doc({
            "doctype": "Party Type",
            "party_type": "Supplier",
            "account_type": "Payable",
        }).insert(ignore_permissions=True)

    # UOMs
    for uom_name in ("Unit", "Hour", "Nos", "Kg"):
        if not frappe.db.exists("UOM", uom_name):
            frappe.get_doc({"doctype": "UOM", "uom_name": uom_name}).insert(
                ignore_permissions=True
            )

    # Territories (tree — need a root first)
    if not frappe.db.exists("Territory", "All Territories"):
        frappe.get_doc({
            "doctype": "Territory",
            "territory_name": "All Territories",
            "is_group": 1,
        }).insert(ignore_permissions=True)
    if not frappe.db.exists("Territory", "Switzerland"):
        frappe.get_doc({
            "doctype": "Territory",
            "territory_name": "Switzerland",
            "parent_territory": "All Territories",
            "is_group": 0,
        }).insert(ignore_permissions=True)

    # Customer Groups (tree)
    if not frappe.db.exists("Customer Group", "All Customer Groups"):
        frappe.get_doc({
            "doctype": "Customer Group",
            "customer_group_name": "All Customer Groups",
            "is_group": 1,
        }).insert(ignore_permissions=True)
    if not frappe.db.exists("Customer Group", "Commercial"):
        frappe.get_doc({
            "doctype": "Customer Group",
            "customer_group_name": "Commercial",
            "parent_customer_group": "All Customer Groups",
            "is_group": 0,
        }).insert(ignore_permissions=True)

    # Item Groups (tree)
    if not frappe.db.exists("Item Group", "All Item Groups"):
        frappe.get_doc({
            "doctype": "Item Group",
            "item_group_name": "All Item Groups",
            "is_group": 1,
        }).insert(ignore_permissions=True)
    if not frappe.db.exists("Item Group", "Services"):
        frappe.get_doc({
            "doctype": "Item Group",
            "item_group_name": "Services",
            "parent_item_group": "All Item Groups",
            "is_group": 0,
        }).insert(ignore_permissions=True)
    if not frappe.db.exists("Item Group", "Products"):
        frappe.get_doc({
            "doctype": "Item Group",
            "item_group_name": "Products",
            "parent_item_group": "All Item Groups",
            "is_group": 0,
        }).insert(ignore_permissions=True)

    # Price Lists — Sales Invoices require a selling price list
    if not frappe.db.exists("Price List", "Standard Selling"):
        frappe.get_doc({
            "doctype": "Price List",
            "price_list_name": "Standard Selling",
            "currency": "CHF",
            "selling": 1,
            "buying": 0,
            "enabled": 1,
        }).insert(ignore_permissions=True)


def _ensure_supplier(supplier_name: str) -> str:
    if frappe.db.exists("Supplier", supplier_name):
        return supplier_name
    doc = frappe.get_doc({
        "doctype": "Supplier",
        "supplier_name": supplier_name,
        "supplier_group": "Services",
        "country": "Switzerland",
    })
    doc.insert(ignore_permissions=True)
    return doc.name


def _ensure_customer(spec: dict) -> str:
    if frappe.db.exists("Customer", spec["customer_name"]):
        return spec["customer_name"]
    doc = frappe.get_doc({
        "doctype": "Customer",
        "customer_name": spec["customer_name"],
        "customer_group": spec.get("customer_group", "Commercial"),
        "territory": spec.get("territory", "Switzerland"),
    })
    doc.insert(ignore_permissions=True)
    return doc.name


def _ensure_item(spec: dict, company: str) -> str:
    code = spec["item_code"]
    if frappe.db.exists("Item", code):
        return code
    doc = frappe.get_doc({
        "doctype": "Item",
        "item_code": code,
        "item_name": spec["item_name"],
        "item_group": spec.get("item_group", "Services"),
        "is_stock_item": spec.get("is_stock_item", 0),
        "stock_uom": spec.get("stock_uom", "Unit"),
        "standard_rate": spec.get("default_unit_price", 0),
    })
    doc.insert(ignore_permissions=True)
    return doc.name


def _resolve_account(account_label: str, company: str) -> str:
    """Convert "6500 - Charges d'administration" to the full Frappe name.

    Strategy:
    1. Try exact name "{account_label} - {abbr}".
    2. Extract account_number from the label prefix, check remap table,
       then look up by account_number in DB.
    """
    abbr = frappe.db.get_value("Company", company, "abbr")
    full = f"{account_label} - {abbr}"
    if frappe.db.exists("Account", full):
        return full

    # Extract number prefix ("6500 - ..." -> "6500")
    parts = account_label.split(" - ", 1)
    number = parts[0].strip()

    # Apply remap if number is missing in this chart
    number = _ACCOUNT_NUMBER_REMAP.get(number, number)

    names = frappe.db.get_all(
        "Account",
        filters={"company": company, "account_number": number},
        pluck="name",
        limit_page_length=1,
    )
    if names:
        return names[0]

    raise frappe.DoesNotExistError(
        f"Account '{account_label}' (number={number}) not found for company '{company}'"
    )


def _get_cost_center(company: str) -> str:
    """Return the main cost center for the company (non-group, first found)."""
    cached = getattr(frappe.local, "_ledgr_cc", {})
    if company in cached:
        return cached[company]
    cc = frappe.db.get_all(
        "Cost Center",
        filters={"company": company, "is_group": 0},
        pluck="name",
        limit_page_length=1,
    )
    return cc[0] if cc else ""


def _materialize_purchase_invoice(op: dict, company: str) -> None:
    expense_account = _resolve_account(op["expense_account"], company)
    creditors = _resolve_account("2000 - Dettes résultant d'achats et de prestations de services", company)
    cost_center = _get_cost_center(company)

    taxes = []
    tva_rate = op.get("tva_rate", 0)
    if tva_rate > 0:
        tva_account = _resolve_account(
            "1170 - Impôt préalable TVA sur matériel, marchandises et prestations de services",
            company,
        )
        taxes = [{
            "charge_type": "On Net Total",
            "account_head": tva_account,
            "description": f"TVA {tva_rate}%",
            "rate": tva_rate,
            "category": "Total",
            "add_deduct_tax": "Add",
            "cost_center": cost_center,
        }]

    # Use in_import flag to bypass date validation for historical posting dates.
    # The posting_date field default is "today" which would reject past dates.
    prev_in_import = frappe.flags.in_import
    frappe.flags.in_import = True
    try:
        pi_doc = frappe.get_doc({
            "doctype": "Purchase Invoice",
            "company": company,
            "supplier": op["supplier_name"],
            "posting_date": op["posting_date"],
            "due_date": op["posting_date"],
            "credit_to": creditors,
            "cost_center": cost_center,
            "items": [{
                "item_name": op["supplier_name"],
                "description": f"Facture {op['supplier_name']} {op['posting_date']}",
                "qty": 1,
                "rate": op["net_amount"],
                "expense_account": expense_account,
                "cost_center": cost_center,
                "uom": "Unit",
                "stock_uom": "Unit",
                "conversion_factor": 1,
            }],
            "taxes": taxes,
        })
        pi_doc.insert(ignore_permissions=True)
        if op.get("submit"):
            pi_doc.submit()
    finally:
        frappe.flags.in_import = prev_in_import


def _materialize_sales_invoice(op: dict, company: str) -> None:
    debtors = _resolve_account("1100 - Créances résultant de ventes et prestations de services", company)
    cost_center = _get_cost_center(company)
    items = []
    for line in op["items"]:
        income = _resolve_account(line["income_account"], company)
        items.append({
            "item_code": line["item_code"],
            "qty": line["qty"],
            "rate": line["rate"],
            "income_account": income,
            "cost_center": cost_center,
        })

    taxes = []
    tva_rate = op.get("tva_rate", 0)
    if tva_rate > 0:
        tva_account = _resolve_account("2200 - TVA due", company)
        taxes = [{
            "charge_type": "On Net Total",
            "account_head": tva_account,
            "description": f"TVA {tva_rate}%",
            "rate": tva_rate,
            "category": "Total",
            "add_deduct_tax": "Add",
            "cost_center": cost_center,
        }]

    prev_in_import = frappe.flags.in_import
    frappe.flags.in_import = True
    try:
        si_doc = frappe.get_doc({
            "doctype": "Sales Invoice",
            "company": company,
            "customer": op["customer_name"],
            "posting_date": op["posting_date"],
            "due_date": op["posting_date"],
            "debit_to": debtors,
            "cost_center": cost_center,
            "selling_price_list": "Standard Selling",
            "price_list_currency": "CHF",
            "plc_conversion_rate": 1,
            "items": items,
            "taxes": taxes,
        })
        si_doc.insert(ignore_permissions=True)
        if op.get("submit"):
            si_doc.submit()
    finally:
        frappe.flags.in_import = prev_in_import


def _materialize_journal_entry(op: dict, company: str) -> None:
    cost_center = _get_cost_center(company)
    accounts_payload = []
    for line in op["lines"]:
        account = _resolve_account(line["account"], company)
        entry = {
            "account": account,
            "debit_in_account_currency": line.get("debit", 0),
            "credit_in_account_currency": line.get("credit", 0),
        }
        # P&L accounts require a cost center
        root_type = frappe.db.get_value("Account", account, "root_type")
        if root_type in ("Income", "Expense") and cost_center:
            entry["cost_center"] = cost_center
        accounts_payload.append(entry)
    je_doc = frappe.get_doc({
        "doctype": "Journal Entry",
        "company": company,
        "posting_date": op["posting_date"],
        "voucher_type": "Journal Entry",
        "title": op.get("title", "Paie"),
        "accounts": accounts_payload,
    })
    je_doc.insert(ignore_permissions=True)
    je_doc.submit()


def _materialize_op(op: dict, company: str) -> None:
    dt = op["doctype"]
    if dt == "Purchase Invoice":
        _materialize_purchase_invoice(op, company)
    elif dt == "Sales Invoice":
        _materialize_sales_invoice(op, company)
    elif dt == "Journal Entry":
        _materialize_journal_entry(op, company)
    else:
        raise ValueError(f"Unknown doctype: {dt}")


def _seed_profile(profile_module, company: str) -> int:
    """Seed all parties + items + operations from a profile module."""
    # Suppliers
    for supplier in profile_module.SUPPLIERS:
        _ensure_supplier(supplier["supplier_name"])

    # Customers
    for customer in profile_module.CUSTOMERS:
        _ensure_customer(customer)

    # Items
    for item in profile_module.ITEMS:
        _ensure_item(item, company)

    # Operations
    ops = profile_module.generate_operations()
    count = 0
    for op in ops:
        try:
            _materialize_op(op, company)
            count += 1
        except Exception as exc:
            frappe.logger("ledgr_demo").error(
                f"seed: failed to materialize {op.get('doctype')} on {op.get('posting_date')}: {exc}"
            )
    return count


def run_seed() -> dict:
    logger = frappe.logger("ledgr_demo")
    random.seed(SEED)

    logger.info("seed: wiping previous demo data")
    run_wipe()

    logger.info("seed: ensuring group fixtures (UOM, Territory, Customer Group, Item Group)")
    _ensure_group_fixtures()

    stats: dict[str, Any] = {"companies_created": [], "operations_seeded": {}}

    for spec in COMPANIES:
        name = _create_company(spec)
        stats["companies_created"].append(name)
        logger.info(f"seed: created Company {name}")

    # Configure companies after chart is seeded (hook runs on insert)
    for spec in COMPANIES:
        _configure_company(spec["name"])
        logger.info(f"seed: configured Company {spec['name']}")

    # FID profile
    from ledgr_demo.profiles import fiduciary
    count_fid = _seed_profile(fiduciary, "Fiduciaire Demo SA")
    stats["operations_seeded"]["Fiduciaire Demo SA"] = count_fid
    logger.info(f"seed: {count_fid} ops materialized for FID")

    # BDL profile — implemented in task 9
    try:
        from ledgr_demo.profiles import bakery
        count_bdl = _seed_profile(bakery, "Boulangerie du Lac SA")
        stats["operations_seeded"]["Boulangerie du Lac SA"] = count_bdl
        logger.info(f"seed: {count_bdl} ops materialized for BDL")
    except ImportError:
        logger.info("seed: bakery profile not yet implemented, skipping BDL ops")

    return stats
