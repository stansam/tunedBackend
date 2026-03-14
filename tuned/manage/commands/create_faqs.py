"""
create_faqs — seed frequently asked questions.

Usage:
    flask create-faqs
"""
import logging
import click
from flask.cli import with_appcontext

from tuned.dtos import FaqDTO
from tuned.interface import Services
from tuned.manage.data import faqs_dict
from tuned.repository.exceptions import AlreadyExists, DatabaseError

logger = logging.getLogger(__name__)


@click.command("create-faqs")
@with_appcontext
def create_faqs() -> None:
    """Seed FAQ entries."""
    services = Services()

    created = skipped = failed = 0
    click.echo("Seeding FAQs…")

    for entry in faqs_dict:
        try:
            dto = FaqDTO(
                question=entry["question"],
                answer=entry["answer"],
                category=entry.get("category", "General"),
                order=entry.get("order", 0),
            )
            services.faq.create_faq(dto)
            click.echo(f"  ✓ Created FAQ [{entry.get('category', 'General')}]: {entry['question'][:60]}…")
            created += 1
        except AlreadyExists:
            click.echo(f"  ⚠ Skipped (already exists): {entry['question'][:60]}…")
            skipped += 1
        except Exception as exc:
            logger.exception("Failed to create FAQ: %s", entry.get("question", ""))
            click.echo(f"  ✗ Error: {exc}")
            failed += 1

    click.echo(f"\nFAQs — created: {created}, skipped: {skipped}, failed: {failed}")