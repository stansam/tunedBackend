"""Admin blog post API views.

Endpoints:
    POST   /admin/blogs/list                        → list all posts (admin, paginated)
    GET    /admin/blogs/stats                       → KPI stats
    POST   /admin/blogs/posts                       → create post
    GET    /admin/blogs/posts/<slug>                → get post by slug
    PATCH  /admin/blogs/posts/<post_id>             → update post
    DELETE /admin/blogs/posts/<post_id>             → soft-delete post
    PATCH  /admin/blogs/posts/<post_id>/publish     → toggle published
    PATCH  /admin/blogs/posts/<post_id>/feature     → toggle featured
    GET    /admin/blogs/posts/<post_id>/comments    → list post comments
"""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone

from flask import request
from flask.views import MethodView
from flask_login import current_user, login_required
from marshmallow import ValidationError

from tuned.apis.admin.schemas.blogs import (
    AdminBlogPostListRequestSchema,
    AdminCreateBlogPostSchema,
    AdminToggleFeaturedSchema,
    AdminTogglePublishSchema,
    AdminUpdateBlogPostSchema,
)
from tuned.core.logging import get_logger
from tuned.dtos import BlogPostDTO, BlogPostListRequestDTO
from tuned.extensions import db
from tuned.interface.admin.blogs import AdminBlogService
from tuned.repository import Repository
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound
from tuned.utils.decorators import admin_required
from tuned.utils.dependencies import get_services
from tuned.utils.responses import (
    created_response,
    error_response,
    no_content_response,
    success_response,
    validation_error_response,
)

logger = get_logger(__name__)


def _admin_blog_service() -> AdminBlogService:
    return AdminBlogService(repos=Repository(db.session), services=get_services())


# ─────────────────────────────────────────────────────────────────────────────
# Stats
# ─────────────────────────────────────────────────────────────────────────────

class AdminBlogStatsView(MethodView):
    decorators = [login_required, admin_required]

    def get(self):
        try:
            stats = _admin_blog_service().get_stats()
            return success_response(data=asdict(stats))
        except Exception as exc:
            logger.error("[AdminBlogStats.get] %r", exc)
            return error_response("Failed to fetch blog stats", status=500)


# ─────────────────────────────────────────────────────────────────────────────
# Posts list (admin, all statuses)
# ─────────────────────────────────────────────────────────────────────────────

class AdminBlogPostsListView(MethodView):
    """POST /admin/blogs/list – paginated listing of ALL posts (drafts + published)."""
    decorators = [login_required, admin_required]

    def post(self):
        try:
            body = AdminBlogPostListRequestSchema().load(request.get_json() or {})
            req = BlogPostListRequestDTO(
                q=body.get("q"),
                category_id=body.get("category_id"),
                is_published=body.get("is_published"),
                page=body.get("page", 1),
                per_page=body.get("per_page", 10),
                sort=body.get("sort"),
                order=body.get("order"),
            )
            result = _admin_blog_service().list_posts(req)
            return success_response(data=asdict(result))
        except ValidationError as err:
            return validation_error_response(err.messages)
        except DatabaseError as exc:
            logger.error("[AdminBlogPostsList.post] %r", exc)
            return error_response("Failed to list blog posts", status=500)
        except Exception as exc:
            logger.error("[AdminBlogPostsList.post] %r", exc)
            return error_response("Internal server error", status=500)


# ─────────────────────────────────────────────────────────────────────────────
# Post CRUD
# ─────────────────────────────────────────────────────────────────────────────

class AdminBlogPostsCollectionView(MethodView):
    """POST /admin/blogs/posts – create a new blog post."""
    decorators = [login_required, admin_required]

    def post(self):
        try:
            validated = AdminCreateBlogPostSchema().load(request.get_json() or {})
            dto = BlogPostDTO(
                title=validated["title"],
                content=validated["content"],
                author=validated["author"],
                category_id=validated["category_id"],
                excerpt=validated.get("excerpt", ""),
                featured_image_id=validated.get("featured_image_id"),
                meta_description=validated.get("meta_description", ""),
                is_published=validated.get("is_published", False),
                is_featured=validated.get("is_featured", False),
                tags=validated.get("tags", []),
                published_at=datetime.now(timezone.utc) if validated.get("is_published") else None,
                created_by=str(current_user.id),
            )
            result = _admin_blog_service().create_post(
                dto,
                actor_id=str(current_user.id),
                ip_address=request.remote_addr or "system",
                user_agent=request.headers.get("User-Agent", "system"),
            )
            return created_response(data=asdict(result))
        except ValidationError as err:
            return validation_error_response(err.messages)
        except AlreadyExists:
            return error_response("A post with this title already exists", status=409)
        except DatabaseError as exc:
            logger.error("[AdminBlogPosts.post] %r", exc)
            return error_response("Failed to create blog post", status=500)
        except Exception as exc:
            logger.error("[AdminBlogPosts.post] %r", exc)
            return error_response("Internal server error", status=500)


class AdminBlogPostDetailView(MethodView):
    """
    GET    /admin/blogs/posts/<slug>     → fetch post by slug
    PATCH  /admin/blogs/posts/<post_id>  → update post (by ID)
    DELETE /admin/blogs/posts/<post_id>  → soft-delete post (by ID)
    """
    decorators = [login_required, admin_required]

    def get(self, slug: str):
        try:
            result = _admin_blog_service().get_post_by_slug(slug)
            return success_response(data=asdict(result))
        except NotFound:
            return error_response("Blog post not found", status=404)
        except Exception as exc:
            logger.error("[AdminBlogPostDetail.get] slug=%s %r", slug, exc)
            return error_response("Failed to fetch blog post", status=500)

    def patch(self, slug: str):
        """Update a post by its ID (slug param used as post_id from client)."""
        try:
            validated = AdminUpdateBlogPostSchema().load(request.get_json() or {})
            dto = BlogPostDTO(
                title=validated.get("title", ""),
                content=validated.get("content", ""),
                author=validated.get("author", ""),
                category_id=validated.get("category_id", ""),
                excerpt=validated.get("excerpt"),
                featured_image_id=validated.get("featured_image_id"),
                meta_description=validated.get("meta_description"),
                is_published=validated.get("is_published", False),
                is_featured=validated.get("is_featured", False),
                tags=validated.get("tags", []),
                updated_by=str(current_user.id),
            )
            result = _admin_blog_service().update_post(
                slug, dto,
                actor_id=str(current_user.id),
                ip_address=request.remote_addr or "system",
                user_agent=request.headers.get("User-Agent", "system"),
            )
            return success_response(data=asdict(result))
        except ValidationError as err:
            return validation_error_response(err.messages)
        except NotFound:
            return error_response("Blog post not found", status=404)
        except DatabaseError as exc:
            logger.error("[AdminBlogPostDetail.patch] %r", exc)
            return error_response("Failed to update blog post", status=500)
        except Exception as exc:
            logger.error("[AdminBlogPostDetail.patch] %r", exc)
            return error_response("Internal server error", status=500)

    def delete(self, slug: str):
        """Soft-delete a post by its ID."""
        try:
            _admin_blog_service().delete_post(
                slug,
                actor_id=str(current_user.id),
                ip_address=request.remote_addr or "system",
                user_agent=request.headers.get("User-Agent", "system"),
            )
            return no_content_response()
        except NotFound:
            return error_response("Blog post not found", status=404)
        except Exception as exc:
            logger.error("[AdminBlogPostDetail.delete] %r", exc)
            return error_response("Failed to delete blog post", status=500)


# ─────────────────────────────────────────────────────────────────────────────
# Publish / Feature toggles
# ─────────────────────────────────────────────────────────────────────────────

class AdminBlogPostPublishView(MethodView):
    """PATCH /admin/blogs/posts/<post_id>/publish."""
    decorators = [login_required, admin_required]

    def patch(self, post_id: str):
        try:
            validated = AdminTogglePublishSchema().load(request.get_json() or {})
            result = _admin_blog_service().toggle_publish(
                post_id,
                is_published=validated["is_published"],
                actor_id=str(current_user.id),
                ip_address=request.remote_addr or "system",
                user_agent=request.headers.get("User-Agent", "system"),
            )
            return success_response(data=asdict(result))
        except ValidationError as err:
            return validation_error_response(err.messages)
        except NotFound:
            return error_response("Blog post not found", status=404)
        except Exception as exc:
            logger.error("[AdminBlogPostPublish.patch] %r", exc)
            return error_response("Failed to toggle publish status", status=500)


class AdminBlogPostFeatureView(MethodView):
    """PATCH /admin/blogs/posts/<post_id>/feature."""
    decorators = [login_required, admin_required]

    def patch(self, post_id: str):
        try:
            validated = AdminToggleFeaturedSchema().load(request.get_json() or {})
            result = _admin_blog_service().toggle_featured(
                post_id,
                is_featured=validated["is_featured"],
                actor_id=str(current_user.id),
                ip_address=request.remote_addr or "system",
                user_agent=request.headers.get("User-Agent", "system"),
            )
            return success_response(data=asdict(result))
        except ValidationError as err:
            return validation_error_response(err.messages)
        except NotFound:
            return error_response("Blog post not found", status=404)
        except Exception as exc:
            logger.error("[AdminBlogPostFeature.patch] %r", exc)
            return error_response("Failed to toggle featured status", status=500)


# ─────────────────────────────────────────────────────────────────────────────
# Post comments listing (admin – all approved + pending)
# ─────────────────────────────────────────────────────────────────────────────

class AdminBlogPostCommentsView(MethodView):
    """GET /admin/blogs/posts/<post_id>/comments."""
    decorators = [login_required, admin_required]

    def get(self, post_id: str):
        try:
            comments = _admin_blog_service().get_post_comments(post_id)
            return success_response(data=[asdict(c) for c in comments])
        except Exception as exc:
            logger.error("[AdminBlogPostComments.get] post_id=%s %r", post_id, exc)
            return error_response("Failed to fetch comments", status=500)
