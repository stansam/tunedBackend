"""
create_users — seed sample client accounts.

Usage:
    flask create-users
"""
import logging
import click
from flask.cli import with_appcontext

from tuned.dtos import CreateUserDTO
from tuned.interface import Services
from tuned.manage.data import users_dict
from tuned.repository.exceptions import AlreadyExists, DatabaseError
from tuned.models.enums import GenderEnum

logger = logging.getLogger(__name__)


@click.command("create-users")
@with_appcontext
def create_users() -> None:
    """Seed sample client user accounts."""
    services = Services()
    created = skipped = failed = 0

    for entry in users_dict:
        email = entry.get("email", "")
        try:
            # Resolve gender enum if provided as string
            gender_raw = entry.get("gender")
            gender = GenderEnum[gender_raw] if gender_raw else GenderEnum.UNKOWN

            dto = CreateUserDTO(
                username=entry["username"],
                email=email,
                password=entry["password"],
                first_name=entry["first_name"],
                last_name=entry["last_name"],
                gender=gender,
                email_verified=entry.get("email_verified", False),
            )
            services.user.create_user(dto)
            click.echo(f"  ✓ Created user: {email}")
            created += 1
        except ValueError:
            click.echo(f"  ⚠ Skipped user (already exists): {email}")
            skipped += 1
        except Exception as exc:
            logger.exception("Failed to create user %s", email)
            click.echo(f"  ✗ Error creating user {email}: {exc}")
            failed += 1

    click.echo(f"\nUsers — created: {created}, skipped: {skipped}, failed: {failed}")