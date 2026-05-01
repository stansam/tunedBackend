import logging
import click
from datetime import datetime
from typing import cast, Dict, Any, Optional
from flask.cli import with_appcontext

from tuned.dtos import BlogCategoryDTO, BlogPostDTO
from tuned.utils.dependencies import get_services
from tuned.manage.data import blogCategories, blogPosts
from tuned.models import BlogCategory, Tag
from tuned.extensions import db
from tuned.repository.exceptions import AlreadyExists, DatabaseError

logger = logging.getLogger(__name__)


def _build_blog_category_map() -> dict[str, str]:
    cats = db.session.query(BlogCategory).all()
    return {str(cat.slug): str(cat.id) for cat in cats}


@click.command("create-blogs")
@with_appcontext
def create_blogs() -> None:
    services = get_services()

    bc_created = bc_skipped = 0
    click.echo("Seeding blog categories…")

    for entry_cat in blogCategories:
        try:
            category_dto = BlogCategoryDTO(
                name=str(entry_cat["name"]),
                slug=str(entry_cat["slug"]),
                description=str(entry_cat.get("description", "")),
            )
            services.blog_category.create_category(category_dto)
            click.echo(f"  ✓ Created blog category: {entry_cat['name']}")
            bc_created += 1
        except AlreadyExists:
            click.echo(f"  ⚠ Skipped (already exists): {entry_cat['name']}")
            bc_skipped += 1
        except Exception as exc:
            logger.exception("Failed to create blog category %s", entry_cat.get("name"))
            click.echo(f"  ✗ Error: {exc}")

    click.echo(
        f"Blog Categories — created: {bc_created}, skipped: {bc_skipped}"
    )

    category_map: dict[str, str] = _build_blog_category_map()

    bp_created = bp_skipped = bp_failed = 0
    click.echo("\nSeeding blog posts…")

    for entry_post in blogPosts:
        category_slug = str(entry_post.get("category_slug", ""))
        category_id = category_map.get(category_slug)

        if not category_id:
            click.echo(
                f"  ✗ Blog category slug '{category_slug}' not found — "
                f"skipping post: {str(entry_post['title'])[:60]}"
            )
            bp_failed += 1
            continue

        try:
            published_at_raw = entry_post.get("published_at")
            published_at_dt: Optional[datetime] = None
            if isinstance(published_at_raw, str):
                published_at_dt = datetime.fromisoformat(published_at_raw)

            post_dto = BlogPostDTO(
                title=str(entry_post["title"]),
                content=str(entry_post["content"]),
                author=str(entry_post["author"]),
                category_id=str(category_id),
                excerpt=str(entry_post.get("excerpt", "")),
                featured_image=str(entry_post.get("featured_image", "")),
                meta_description=str(entry_post.get("meta_description", "")),
                is_published=bool(entry_post.get("is_published", False)),
                is_featured=bool(entry_post.get("is_featured", False)),
                published_at=published_at_dt,
            )
            post_resp = services.blog_post.create_post(post_dto)
            click.echo(f"  ✓ Created blog post: {str(entry_post['title'])[:60]}")
            bp_created += 1

            tag_string = str(entry_post.get("tags", ""))
            if tag_string:
                from tuned.models import BlogPost as BlogPostModel
                post_record = db.session.query(BlogPostModel).filter_by(
                    id=post_resp.id
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
            click.echo(f"  ⚠ Skipped (already exists): {str(entry_post['title'])[:60]}")
            bp_skipped += 1
        except Exception as exc:
            db.session.rollback()
            logger.exception("Failed to create blog post %s", entry_post.get("title"))
            click.echo(f"  ✗ Error creating post '{entry_post.get('title', '')}': {exc}")
            bp_failed += 1

    click.echo(
        f"\nBlog Posts — created: {bp_created}, skipped: {bp_skipped}, failed: {bp_failed}"
    )