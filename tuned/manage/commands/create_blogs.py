import logging
import click
from flask.cli import with_appcontext

from tuned.dtos import BlogCategoryDTO, BlogPostDTO
from tuned.interface import Services
from tuned.manage.data import blogCategories, blogPosts
from tuned.models import BlogCategory, Tag
from tuned.extensions import db
from tuned.repository.exceptions import AlreadyExists, DatabaseError

logger = logging.getLogger(__name__)


def _build_blog_category_map() -> dict[str, str]:
    cats = db.session.query(BlogCategory).all()
    return {cat.slug: cat.id for cat in cats}


@click.command("create-blogs")
@with_appcontext
def create_blogs() -> None:
    services = Services()

    bc_created = bc_skipped = 0
    click.echo("Seeding blog categories…")

    for entry in blogCategories:
        try:
            dto = BlogCategoryDTO(
                name=entry["name"],
                slug=entry["slug"],
                description=entry.get("description", ""),
            )
            services.blog_category.create_category(dto)
            click.echo(f"  ✓ Created blog category: {entry['name']}")
            bc_created += 1
        except AlreadyExists:
            click.echo(f"  ⚠ Skipped (already exists): {entry['name']}")
            bc_skipped += 1
        except Exception as exc:
            logger.exception("Failed to create blog category %s", entry.get("name"))
            click.echo(f"  ✗ Error: {exc}")

    click.echo(
        f"Blog Categories — created: {bc_created}, skipped: {bc_skipped}"
    )

    category_map = _build_blog_category_map()

    bp_created = bp_skipped = bp_failed = 0
    click.echo("\nSeeding blog posts…")

    for entry in blogPosts:
        category_slug = entry.get("category_slug", "")
        category_id = category_map.get(category_slug)

        if not category_id:
            click.echo(
                f"  ✗ Blog category slug '{category_slug}' not found — "
                f"skipping post: {entry['title'][:60]}"
            )
            bp_failed += 1
            continue

        try:
            dto = BlogPostDTO(
                title=entry["title"],
                content=entry["content"],
                author=entry["author"],
                category_id=category_id,
                excerpt=entry.get("excerpt", ""),
                featured_image=entry.get("featured_image", ""),
                meta_description=entry.get("meta_description", ""),
                is_published=entry.get("is_published", False),
                is_featured=entry.get("is_featured", False),
                published_at=entry.get("published_at"),
            )
            post_obj = services.blog_post.create_post(dto)
            click.echo(f"  ✓ Created blog post: {entry['title'][:60]}")
            bp_created += 1

            tag_string = entry.get("tags", "")
            if tag_string:
                from tuned.models import BlogPost as BlogPostModel
                post_record = db.session.query(BlogPostModel).filter_by(
                    id=post_obj.id
                ).first()
                if post_record:
                    tag_objects = Tag.parse_tags(tag_string)
                    for tag in tag_objects:
                        if tag not in post_record.tag_list:
                            post_record.tag_list.append(tag)
                            tag.usage_count += 1
                    db.session.commit()
                    click.echo(
                        f"    ↳ Tags applied: {', '.join(t.name for t in tag_objects)}"
                    )

        except AlreadyExists:
            click.echo(f"  ⚠ Skipped (already exists): {entry['title'][:60]}")
            bp_skipped += 1
        except Exception as exc:
            db.session.rollback()
            logger.exception("Failed to create blog post %s", entry.get("title"))
            click.echo(f"  ✗ Error creating post '{entry.get('title', '')}': {exc}")
            bp_failed += 1

    click.echo(
        f"\nBlog Posts — created: {bp_created}, skipped: {bp_skipped}, failed: {bp_failed}"
    )