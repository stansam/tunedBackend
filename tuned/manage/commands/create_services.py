import logging
import click
from flask.cli import with_appcontext

from tuned.dtos import ServiceCategoryDTO, ServiceDTO
from tuned.utils.dependencies import get_services
from tuned.manage.data import (
    service_categories_dict,
    service_category_descriptions_dict,
    service_to_pricing_category_dict,
)
from tuned.models import PricingCategory, ServiceCategory
from tuned.extensions import db
from tuned.repository.exceptions import AlreadyExists #, DatabaseError
from tuned.core.logging import get_logger

logger: logging.Logger = get_logger(__name__)


from typing import cast, Any

def _build_pricing_cat_map() -> dict[str, str]:
    cats = db.session.query(PricingCategory).all()
    return {str(c.name): str(c.id) for c in cats}


def _build_service_cat_map() -> dict[str, str]:
    cats = db.session.query(ServiceCategory).all()
    return {str(c.name): str(c.id) for c in cats}


@click.command("create-services")
@with_appcontext
def create_services() -> None:
    services = get_services()

    pricing_cat_map = _build_pricing_cat_map()
    if not pricing_cat_map:
        click.echo("✗ No pricing categories found — run `flask create-prices` first.")
        return

    # --- Service Categories ---
    sc_created = sc_skipped = 0
    click.echo("Seeding service categories…")

    for order_idx, (cat_name, _) in enumerate(service_categories_dict.items(), start=1):
        description = service_category_descriptions_dict.get(cat_name, "")
        try:
            sc_dto = ServiceCategoryDTO(
                name=str(cat_name),
                description=str(description),
                order=int(order_idx),
            )
            services.service_category.create_category(sc_dto)
            click.echo(f"  ✓ Created service category: {cat_name}")
            sc_created += 1
        except AlreadyExists:
            click.echo(f"  ⚠ Skipped (already exists): {cat_name}")
            sc_skipped += 1
        except Exception as exc:
            logger.exception("Failed to create service category %s", cat_name)
            click.echo(f"  ✗ Error: {exc}")

    click.echo(
        f"Service Categories — created: {sc_created}, skipped: {sc_skipped}"
    )

    service_cat_map = _build_service_cat_map()

    svc_created = svc_skipped = svc_failed = 0
    click.echo("\nSeeding services…")

    for cat_name, service_list in service_categories_dict.items():
        category_id = service_cat_map.get(cat_name)
        if not category_id:
            click.echo(f"  ✗ Service category not found: '{cat_name}' — skipping its services.")
            continue

        for svc_name, svc_description in service_list:
            pricing_cat_name = service_to_pricing_category_dict.get(svc_name)
            pricing_cat_id = pricing_cat_map.get(pricing_cat_name) if pricing_cat_name else None

            if not pricing_cat_id:
                click.echo(
                    f"  ✗ Pricing category '{pricing_cat_name}' not found for service '{svc_name}' — skipping."
                )
                svc_failed += 1
                continue

            try:
                svc_dto = ServiceDTO(
                    name=str(svc_name),
                    description=str(svc_description),
                    category_id=str(category_id),
                    featured=False,
                    pricing_category_id=str(pricing_cat_id),
                    is_active=True,
                )
                services.service.create_service(svc_dto)
                click.echo(f"  ✓ Created service: {svc_name}")
                svc_created += 1
            except AlreadyExists:
                click.echo(f"  ⚠ Skipped (already exists): {svc_name}")
                svc_skipped += 1
            except Exception as exc:
                logger.exception("Failed to create service %s", svc_name)
                click.echo(f"  ✗ Error creating service {svc_name}: {exc}")
                svc_failed += 1

    click.echo(
        f"Services — created: {svc_created}, skipped: {svc_skipped}, failed: {svc_failed}"
    )