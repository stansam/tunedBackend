from flask.cli import with_appcontext
import click 
from tuned.utils.dependencies import get_services
from tuned.dtos import CreateUserDTO
from tuned.dtos.base import BaseRequestDTO

@click.command("createsuperuser")
@click.option("--username", prompt=True)
@click.option("--first-name", prompt=True)
@click.option("--last-name", prompt=True)
@click.option("--email", prompt=True)
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
@with_appcontext
def create_superuser(username: str, first_name: str, last_name: str, email: str, password: str) -> None:
    try:
        user_service = get_services().user
        try:
            user = user_service.get_user_by_email(email)
            if user:
                click.echo("Admin user already exists")
                return
        except Exception:
            pass

        admin_dto = CreateUserDTO(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_admin=True,
            email_verified=True
        )

        locale = BaseRequestDTO(ip_address="cli", user_agent="cli-tool")
        admin_user_resp = user_service.create_user(admin_dto, locale)
        if admin_user_resp:
            click.echo(f"Admin user created successfully. Email: {admin_user_resp['email']}")
        else:
            click.echo("Admin user creation failed")
    except Exception as e:
        click.echo(f"Admin user creation failed: {e}")