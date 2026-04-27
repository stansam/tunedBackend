import logging
import click
from flask.cli import with_appcontext

from tuned.dtos import AcademicLevelDTO, DeadlineDTO
from tuned.interface import Services
from tuned.manage.data import academic_levels_dict, deadlines_dict
from tuned.repository.exceptions import AlreadyExists #, DatabaseError
from tuned.core.logging import get_logger

logger: logging.Logger = get_logger(__name__)


@click.command("create-content")
@with_appcontext
def create_content() -> None:
    services = Services()

    al_created = al_skipped = al_failed = 0
    click.echo("Seeding academic levels…")
    for entry in academic_levels_dict:
        try:
            dto = AcademicLevelDTO(name=entry["name"], order=entry.get("order", 0))
            services.academic_level.create_academic_level(dto)
            click.echo(f"  ✓ Created academic level: {entry['name']}")
            al_created += 1
        except AlreadyExists:
            click.echo(f"  ⚠ Skipped (already exists): {entry['name']}")
            al_skipped += 1
        except Exception as exc:
            logger.exception("Failed to create academic level %s", entry.get("name"))
            click.echo(f"  ✗ Error: {exc}")
            al_failed += 1

    click.echo(
        f"Academic Levels — created: {al_created}, skipped: {al_skipped}, failed: {al_failed}"
    )

    dl_created = dl_skipped = dl_failed = 0
    click.echo("\nSeeding deadlines…")
    for entry in deadlines_dict:
        try:
            dto = DeadlineDTO(
                name=entry["name"],
                hours=entry["hours"],
                order=entry.get("order", 0),
            )
            services.deadline.create_deadline(dto)
            click.echo(f"  ✓ Created deadline: {entry['name']}")
            dl_created += 1
        except AlreadyExists:
            click.echo(f"  ⚠ Skipped (already exists): {entry['name']}")
            dl_skipped += 1
        except Exception as exc:
            logger.exception("Failed to create deadline %s", entry.get("name"))
            click.echo(f"  ✗ Error: {exc}")
            dl_failed += 1

    click.echo(
        f"Deadlines — created: {dl_created}, skipped: {dl_skipped}, failed: {dl_failed}"
    )