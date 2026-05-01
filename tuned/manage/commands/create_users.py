import logging
import click
from flask.cli import with_appcontext

from tuned.dtos import CreateUserDTO
from tuned.dtos.base import BaseRequestDTO
from tuned.utils.dependencies import get_services
from tuned.manage.data import users_dict
from tuned.models.enums import GenderEnum
# from tuned.repository.exceptions import AlreadyExists, DatabaseError
from tuned.core.logging import get_logger

logger: logging.Logger = get_logger(__name__)

@click.command("create-users")
@with_appcontext
def create_users() -> None:
    services = get_services()
    created = skipped = failed = 0

    for entry in users_dict:
        email = str(entry.get("email", ""))
        try:
            gender_raw = entry.get("gender")
            gender = GenderEnum[str(gender_raw)] if gender_raw and str(gender_raw) in GenderEnum.__members__ else GenderEnum.UNKNOWN

            dto = CreateUserDTO(
                username=str(entry["username"]),
                email=email,
                password=str(entry["password"]),
                first_name=str(entry["first_name"]),
                last_name=str(entry["last_name"]),
                gender=gender,
                email_verified=bool(entry.get("email_verified", False)),
            )
            locale = BaseRequestDTO(
                ip_address="127.0.0.1",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            services.user.create_user(dto, locale)
            click.echo(f"  ✓ Created user: {email}")
            created += 1
        except (ValueError, KeyError):
            click.echo(f"  ⚠ Skipped user (already exists or invalid gender): {email}")
            skipped += 1
        except Exception as exc:
            logger.exception("Failed to create user %s", email)
            click.echo(f"  ✗ Error creating user {email}: {exc}")
            failed += 1

    click.echo(f"\nUsers — created: {created}, skipped: {skipped}, failed: {failed}")