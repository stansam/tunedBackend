"""
manage_tables — inspect and optionally empty database tables.

Usage:
    flask manage-tables --list
    flask manage-tables --empty <table_name>   [--yes]
    flask manage-tables --empty-all            [--yes]
"""
import logging
import click
from flask.cli import with_appcontext
from sqlalchemy import text, inspect as sa_inspect

from tuned.extensions import db

logger = logging.getLogger(__name__)

# Tables that are considered "seed data" — targeted by --empty-all
SEED_TABLES = [
    "blog_post_tags",
    "sample_tags",
    "service_tags",
    "blog_comment",
    "comment_reaction",
    "blog_post",
    "blog_category",
    "faq",
    "testimonial",
    "sample",
    "service",
    "service_category",
    "price_rate",
    "pricing_category",
    "deadline",
    "academic_level",
    "users",
    "tag",
]


def _all_table_names() -> list[str]:
    """Return every table name in the current database."""
    inspector = sa_inspect(db.engine)
    return sorted(inspector.get_table_names())


def _row_count(table: str) -> int:
    try:
        result = db.session.execute(text(f"SELECT COUNT(*) FROM `{table}`"))
        return result.scalar() or 0
    except Exception:
        return -1


def _delete_table(table: str) -> int:
    """Delete all rows from a table using DELETE (respects FK constraints).
    Returns number of rows deleted.
    """
    count_before = _row_count(table)
    db.session.execute(text(f"DELETE FROM `{table}`"))
    db.session.commit()
    return count_before if count_before >= 0 else -1


@click.command("manage-tables")
@click.option("--list", "do_list", is_flag=True, default=False,
              help="List all tables with row counts.")
@click.option("--empty", "empty_table", default=None, metavar="TABLE",
              help="Delete all rows from the specified table.")
@click.option("--empty-all", "empty_all", is_flag=True, default=False,
              help="Delete all rows from all seed data tables.")
@click.option("--yes", "-y", is_flag=True, default=False,
              help="Skip confirmation prompts (use with caution).")
@with_appcontext
def manage_tables(do_list: bool, empty_table: str, empty_all: bool, yes: bool) -> None:
    """Inspect and manage database table contents.

    \b
    Examples:
        flask manage-tables --list
        flask manage-tables --empty faq
        flask manage-tables --empty-all --yes
    """
    if not any([do_list, empty_table, empty_all]):
        click.echo("Provide at least one option. Run with --help for usage.")
        return

    all_tables = _all_table_names()

    # --list
    if do_list:
        click.echo(f"\n{'Table':<40} {'Rows':>8}")
        click.echo("─" * 50)
        for tbl in all_tables:
            rows = _row_count(tbl)
            row_str = str(rows) if rows >= 0 else "N/A"
            click.echo(f"  {tbl:<38} {row_str:>8}")
        click.echo(f"\n  Total tables: {len(all_tables)}")

    # --empty <table>
    if empty_table:
        if empty_table not in all_tables:
            click.echo(f"✗ Table '{empty_table}' does not exist. Available tables:")
            for t in all_tables:
                click.echo(f"    {t}")
            return

        if not yes:
            click.confirm(
                f"⚠  This will DELETE ALL ROWS from '{empty_table}'. Continue?",
                abort=True,
            )
        try:
            deleted = _delete_table(empty_table)
            click.echo(f"✓ Emptied '{empty_table}' — {deleted} rows removed.")
        except Exception as exc:
            db.session.rollback()
            logger.exception("Failed to empty table %s", empty_table)
            click.echo(f"✗ Error emptying '{empty_table}': {exc}")

    # --empty-all
    if empty_all:
        if not yes:
            click.confirm(
                f"⚠  This will DELETE ALL ROWS from {len(SEED_TABLES)} seed tables. Continue?",
                abort=True,
            )
        click.echo("\nEmptying seed tables (in FK-safe order)…")
        total_deleted = 0
        had_error = False
        for tbl in SEED_TABLES:
            if tbl not in all_tables:
                click.echo(f"  ⚠ Table '{tbl}' not found — skipping.")
                continue
            try:
                deleted = _delete_table(tbl)
                click.echo(f"  ✓ {tbl:<38} {deleted:>6} rows removed")
                total_deleted += deleted if deleted >= 0 else 0
            except Exception as exc:
                db.session.rollback()
                logger.exception("Failed to empty table %s", tbl)
                click.echo(f"  ✗ {tbl}: {exc}")
                had_error = True

        status = "with errors" if had_error else "successfully"
        click.echo(f"\nAll-tables empty completed {status}. Total rows removed: {total_deleted}")
