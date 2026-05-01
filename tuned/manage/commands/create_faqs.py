import logging
import click
from flask.cli import with_appcontext

from tuned.dtos import FaqDTO
from tuned.utils.dependencies import get_services
from tuned.manage.data import faqs_dict
from tuned.repository.exceptions import AlreadyExists #, DatabaseError
from tuned.core.logging import get_logger

logger: logging.Logger = get_logger(__name__)


@click.command("create-faqs")
@with_appcontext
def create_faqs() -> None:
    services = get_services()

    created = skipped = failed = 0
    click.echo("Seeding FAQs…")

    from typing import cast, Any
    for entry in faqs_dict:
        try:
            faq_dto = FaqDTO(
                question=str(entry["question"]),
                answer=str(entry["answer"]),
                category=str(entry.get("category", "General")),
                order=int(cast(Any, entry.get("order", 0))),
            )
            services.faq.create_faq(faq_dto)
            click.echo(f"  ✓ Created FAQ [{entry.get('category', 'General')}]: {str(cast(Any, entry)['question'])[:60]}…")
            created += 1
        except AlreadyExists:
            click.echo(f"  ⚠ Skipped (already exists): {str(cast(Any, entry)['question'])[:60]}…")
            skipped += 1
        except Exception as exc:
            logger.exception("Failed to create FAQ: %s", entry.get("question", ""))
            click.echo(f"  ✗ Error: {exc}")
            failed += 1

    click.echo(f"\nFAQs — created: {created}, skipped: {skipped}, failed: {failed}")