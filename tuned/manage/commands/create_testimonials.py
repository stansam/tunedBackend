import logging
import click
from flask.cli import with_appcontext

from tuned.dtos import TestimonialDTO
from tuned.interface import Services
from tuned.manage.data import testimonials_dict
from tuned.models import Service, User
from tuned.extensions import db
# from tuned.repository.exceptions import AlreadyExists, DatabaseError
from tuned.core.logging import get_logger

logger: logging.Logger = get_logger(__name__)


def _build_service_map() -> dict[str, str]:
    return {svc.name: svc.id for svc in db.session.query(Service).all()}


def _build_user_map() -> dict[str, str]:
    return {u.username: u.id for u in db.session.query(User).all()}


@click.command("create-testimonials")
@with_appcontext
def create_testimonials() -> None:
    services = Services()
    service_map = _build_service_map()
    user_map = _build_user_map()

    if not service_map:
        click.echo("✗ No services found — run `flask create-services` first.")
        return
    if not user_map:
        click.echo("✗ No users found — run `flask create-users` first.")
        return

    created = skipped = failed = 0
    click.echo("Seeding testimonials…")

    for entry in testimonials_dict:
        service_name = entry.get("service_name", "")
        author_username = entry.get("author_username", "")

        service_id = service_map.get(service_name)
        user_id = user_map.get(author_username)

        if not service_id:
            click.echo(f"  ✗ Service '{service_name}' not found — skipping testimonial.")
            failed += 1
            continue
        if not user_id:
            click.echo(
                f"  ✗ User '{author_username}' not found — skipping testimonial."
            )
            failed += 1
            continue

        try:
            dto = TestimonialDTO(
                user_id=user_id,
                service_id=service_id,
                content=entry["content"],
                rating=entry["rating"],
                is_approved=entry.get("is_approved", False),
            )
            services.testimonial.submit_testimonial(dto)
            click.echo(
                f"  ✓ Created testimonial by '{author_username}' for '{service_name}'"
            )
            created += 1
        except Exception as exc:
            logger.exception(
                "Failed to create testimonial by %s for %s", author_username, service_name
            )
            click.echo(f"  ✗ Error: {exc}")
            failed += 1

    click.echo(
        f"\nTestimonials — created: {created}, skipped: {skipped}, failed: {failed}"
    )