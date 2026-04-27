import logging
import click
from flask.cli import with_appcontext

from tuned.dtos import SampleDTO
from tuned.interface import Services
from tuned.manage.data import samples_dict
from tuned.models import Service, Tag
from tuned.extensions import db
from tuned.repository.exceptions import AlreadyExists, DatabaseError

logger = logging.getLogger(__name__)


def _build_service_map() -> dict[str, str]:
    services = db.session.query(Service).all()
    return {svc.name: svc.id for svc in services}


@click.command("create-samples")
@with_appcontext
def create_samples() -> None:
    services = Services()
    service_map = _build_service_map()

    if not service_map:
        click.echo("✗ No services found — run `flask create-services` first.")
        return

    created = skipped = failed = 0
    click.echo("Seeding samples…")

    for entry in samples_dict:
        service_name = entry.get("service", "")
        service_id = service_map.get(service_name)
        if not service_id:
            click.echo(
                f"  ✗ Service '{service_name}' not found — skipping sample: {entry['title']}"
            )
            failed += 1
            continue

        try:
            dto = SampleDTO(
                title=entry["title"],
                content=entry["content"],
                service_id=service_id,
                excerpt=entry.get("excerpt", ""),
                word_count=entry.get("word_count", 0),
                featured=entry.get("featured", False),
                image=entry.get("image", ""),
            )
            sample_obj = services.sample.create_sample(dto)
            click.echo(f"  ✓ Created sample: {entry['title']}")
            created += 1

            tag_string = entry.get("tags", "")
            if tag_string:
                from tuned.models import Sample as SampleModel
                sample_record = db.session.query(SampleModel).filter_by(
                    id=sample_obj.id
                ).first()
                if sample_record:
                    tag_objects = Tag.parse_tags(tag_string)
                    for tag in tag_objects:
                        if tag not in sample_record.tag_list:
                            sample_record.tag_list.append(tag)
                            tag.usage_count += 1
                    db.session.commit()
                    click.echo(
                        f"    ↳ Tags applied: {', '.join(t.name for t in tag_objects)}"
                    )

        except AlreadyExists:
            click.echo(f"  ⚠ Skipped (already exists): {entry['title']}")
            skipped += 1
        except Exception as exc:
            db.session.rollback()
            logger.exception("Failed to create sample %s", entry.get("title"))
            click.echo(f"  ✗ Error creating sample {entry.get('title')}: {exc}")
            failed += 1

    click.echo(f"\nSamples — created: {created}, skipped: {skipped}, failed: {failed}")