"""
create_prices — seed pricing categories and price rates.

Requires academic levels and deadlines to already exist (run create-content first).

Usage:
    flask create-prices
"""
import logging
import click
from flask.cli import with_appcontext

from tuned.dtos import PricingCategoryDTO, PriceRateDTO
from tuned.interface import Services
from tuned.manage.data import pricing_categories_dict, price_rates_dict, pricing_level_names
from tuned.models import AcademicLevel, Deadline, PricingCategory
from tuned.extensions import db
from tuned.repository.exceptions import AlreadyExists, DatabaseError

logger = logging.getLogger(__name__)


def _build_level_map() -> dict[str, str]:
    """Return {level_name: level_id} for all seeded academic levels."""
    levels = db.session.query(AcademicLevel).all()
    return {lvl.name: lvl.id for lvl in levels}


def _build_deadline_map() -> dict[str, str]:
    """Return {deadline_name: deadline_id} for all seeded deadlines."""
    deadlines = db.session.query(Deadline).all()
    return {d.name: d.id for d in deadlines}


def _build_category_map() -> dict[str, str]:
    """Return {category_name: category_id} for seeded pricing categories."""
    cats = db.session.query(PricingCategory).all()
    return {c.name: c.id for c in cats}


@click.command("create-prices")
@with_appcontext
def create_prices() -> None:
    """Seed pricing categories and per-page price rates."""
    services = Services()

    # --- Pricing Categories ---
    pc_created = pc_skipped = 0
    click.echo("Seeding pricing categories…")
    for entry in pricing_categories_dict:
        try:
            dto = PricingCategoryDTO(
                name=entry["name"],
                description=entry.get("description", ""),
                display_order=entry.get("display_order", 0),
            )
            services.pricing_category.create_category(dto)
            click.echo(f"  ✓ Created pricing category: {entry['name']}")
            pc_created += 1
        except AlreadyExists:
            click.echo(f"  ⚠ Skipped (already exists): {entry['name']}")
            pc_skipped += 1
        except Exception as exc:
            logger.exception("Failed to create pricing category %s", entry.get("name"))
            click.echo(f"  ✗ Error: {exc}")

    click.echo(f"Pricing Categories — created: {pc_created}, skipped: {pc_skipped}")

    # --- Price Rates ---
    level_map = _build_level_map()
    deadline_map = _build_deadline_map()
    category_map = _build_category_map()

    if not level_map:
        click.echo("\n✗ No academic levels found — run `flask create-content` first.")
        return
    if not deadline_map:
        click.echo("\n✗ No deadlines found — run `flask create-content` first.")
        return

    pr_created = pr_skipped = pr_failed = 0
    click.echo("\nSeeding price rates…")

    for category_name, deadline_rates in price_rates_dict.items():
        category_id = category_map.get(category_name)
        if not category_id:
            click.echo(f"  ✗ Pricing category not found: '{category_name}' — skipping its rates.")
            continue

        for deadline_name, prices in deadline_rates.items():
            deadline_id = deadline_map.get(deadline_name)
            if not deadline_id:
                click.echo(f"  ✗ Deadline not found: '{deadline_name}' — skipping.")
                pr_failed += 1
                continue

            for idx, level_name in enumerate(pricing_level_names):
                level_id = level_map.get(level_name)
                if not level_id:
                    click.echo(f"  ✗ Academic level not found: '{level_name}' — skipping.")
                    pr_failed += 1
                    continue

                price = prices[idx]
                try:
                    dto = PriceRateDTO(
                        pricing_category_id=category_id,
                        academic_level_id=level_id,
                        deadline_id=deadline_id,
                        price_per_page=price,
                        is_active=True,
                    )
                    services.price_rate.create_rate(dto)
                    pr_created += 1
                except AlreadyExists:
                    pr_skipped += 1
                except Exception as exc:
                    logger.exception(
                        "Failed to create rate: cat=%s lvl=%s dl=%s",
                        category_name, level_name, deadline_name,
                    )
                    click.echo(f"  ✗ Error creating rate: {exc}")
                    pr_failed += 1

    click.echo(
        f"Price Rates — created: {pr_created}, skipped: {pr_skipped}, failed: {pr_failed}"
    )