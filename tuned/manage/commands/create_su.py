from flask.cli import with_appcontext
from tuned.models import User
from tuned.models.enums import GenderEnum
import click 
from tuned.interface import Services
from tuned.dtos import CreateUserDTO
from tuned.extensions import db

@click.command("createsuperuser")
@click.option("--username", prompt=True)
@click.option("--first-name", prompt=True)
@click.option("--last-name", prompt=True)
@click.option("--email", prompt=True)
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
@with_appcontext
def create_superuser(username, first_name, last_name, email, password) -> str:
    try:
        user_service = Services.user
        user = user_service.get_user_by_email(email)

        if user:
            click.echo("Admin user already exists")
            return

        admin_dto = CreateUserDTO(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_admin=True
        )

        adminUser = user_service.create_user(admin_dto)
        if adminUser:
            click.echo(f"Admin user created successfully. Email:{adminUser.email}")
        else:
            click.echo("Admin user creation failed")
    except Exception as e:
        click.echo(f"Admin user creation failed: {e}")