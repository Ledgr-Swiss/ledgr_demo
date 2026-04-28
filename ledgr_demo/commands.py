"""Bench CLI commands for ledgr_demo.

Registered via hooks.py — accessible as `bench --site <site> seed-demo` etc.
"""
import click
import frappe
from frappe.commands import pass_context, get_site


@click.command("seed-demo")
@pass_context
def seed_demo(context):
    """Wipe then re-create the 2 demo companies with realistic 12-month data."""
    site = get_site(context)
    with frappe.init_site(site):
        frappe.connect()
        try:
            from ledgr_demo.seeder import run_seed
            run_seed()
            frappe.db.commit()
            click.secho("✓ Seed completed", fg="green")
        except Exception as exc:
            frappe.db.rollback()
            click.secho(f"✗ Seed failed: {exc}", fg="red")
            raise


@click.command("wipe-demo")
@click.option("--purge", is_flag=True, default=False,
              help="Drop aussi les mappings (Tax Templates, Salary Component Account, ...) avant la Company")
@pass_context
def wipe_demo(context, purge):
    """Delete the 2 demo companies and all their linked documents."""
    site = get_site(context)
    with frappe.init_site(site):
        frappe.connect()
        try:
            from ledgr_demo.wipe import run_wipe
            run_wipe(purge=purge)
            frappe.db.commit()
            click.secho(f"✓ Wipe completed (purge={purge})", fg="green")
        except Exception as exc:
            frappe.db.rollback()
            click.secho(f"✗ Wipe failed: {exc}", fg="red")
            raise


commands = [seed_demo, wipe_demo]
