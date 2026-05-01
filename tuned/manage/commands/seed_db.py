import logging
from typing import Any
import click
from flask.cli import with_appcontext

from tuned.manage.commands.create_users import create_users as _create_users
from tuned.manage.commands.create_content import create_content as _create_content
from tuned.manage.commands.create_prices import create_prices as _create_prices
from tuned.manage.commands.create_services import create_services as _create_services
from tuned.manage.commands.create_samples import create_samples as _create_samples
from tuned.manage.commands.create_testimonials import create_testimonials as _create_testimonials
from tuned.manage.commands.create_faqs import create_faqs as _create_faqs
from tuned.manage.commands.create_blogs import create_blogs as _create_blogs
from tuned.core.logging import get_logger

logger: logging.Logger = get_logger(__name__)


def _run_step(ctx: click.Context, cmd: Any, label: str) -> None:
    click.echo(f"\n{'─' * 60}")
    click.echo(f"  STEP: {label}")
    click.echo(f"{'─' * 60}")
    ctx.invoke(cmd)


@click.command("seed-db")
@click.pass_context
@with_appcontext
def seed_db(ctx: click.Context) -> None:
    click.echo("=" * 60)
    click.echo("  TUNED DATABASE SEEDER")
    click.echo("=" * 60)

    steps = [
        (_create_users,        "Users"),
        (_create_content,      "Content (Academic Levels + Deadlines)"),
        (_create_prices,       "Prices (Categories + Rates)"),
        (_create_services,     "Services (Categories + Services)"),
        (_create_samples,      "Samples"),
        (_create_testimonials, "Testimonials"),
        (_create_faqs,         "FAQs"),
        (_create_blogs,        "Blog (Categories + Posts)"),
    ]

    for cmd, label in steps:
        try:
            _run_step(ctx, cmd, label)
        except SystemExit:
            pass
        except Exception as exc:
            logger.exception("Seeder step '%s' failed", label)
            click.echo(f"\n✗ Step '{label}' raised an unexpected error: {exc}")
            click.echo("  Continuing with remaining steps…")

    click.echo("\n" + "=" * 60)
    click.echo("  SEEDING COMPLETE")
    click.echo("=" * 60)