import logging
import click
from flask.cli import with_appcontext

from tuned.dtos.payment import AcceptedMethodCreateDTO
from tuned.utils.dependencies import get_services
from tuned.manage.data import accepted_methods_list
from tuned.models import User, AcceptedPaymentMethod
from tuned.models.enums import PaymentMethod
from tuned.extensions import db
from tuned.repository.exceptions import AlreadyExists
from tuned.core.logging import get_logger
from tuned.core.exceptions import NotFound

logger: logging.Logger = get_logger(__name__)

@click.command("create-payment-methods")
@with_appcontext
def create_payment_methods() -> None:
    services = get_services()
    created = skipped = failed = 0
    click.echo("Seeding accepted payment methods…")

    # Retrieve an admin user ID for activity logging, or default to a standard system UUID
    admin_user = None
    try:
        admin_user = services.user._repo.get_admin_user()
    except NotFound:
        pass
    admin_id = str(admin_user.id) if admin_user else "00000000-0000-0000-0000-000000000000"

    for entry in accepted_methods_list:
        name = entry["name"]
        try:
            existing = services._repos.payment.accepted_method.get_by_name(name)
            if existing:
                click.echo(f"  ⚠ Skipped (already exists): {name}")
                skipped += 1
                continue

            dto = AcceptedMethodCreateDTO(
                name=name,
                category=entry["category"],
                details=entry.get("details"),
                is_active=entry.get("is_active", True)
            )

            services.payment.accepted_method.create(dto, admin_id)
            db.session.commit()
            click.echo(f"  ✓ Created payment method: {name}")
            created += 1
        except AlreadyExists:
            db.session.rollback()
            click.echo(f"  ⚠ Skipped (already exists Exception): {name}")
            skipped += 1
        except Exception as exc:
            db.session.rollback()
            logger.exception("Failed to create payment method %s", name)
            click.echo(f"  ✗ Error: {exc}")
            failed += 1

    click.echo(f"\nPayment Methods — created: {created}, skipped: {skipped}, failed: {failed}")
