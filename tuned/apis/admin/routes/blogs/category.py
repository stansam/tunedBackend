"""Admin blog category and comment API views.

Endpoints:
    GET    /admin/blogs/categories                          → list categories (with post counts)
    POST   /admin/blogs/categories                          → create category
    PATCH  /admin/blogs/categories/<category_id>            → update category
    DELETE /admin/blogs/categories/<category_id>            → soft-delete category
    PATCH  /admin/blogs/comments/<comment_id>/approve       → approve/unapprove comment
    DELETE /admin/blogs/comments/<comment_id>               → soft-delete comment
    DELETE /admin/blogs/reactions/<reaction_id>             → soft-delete reaction
"""
from __future__ import annotations

from dataclasses import asdict

from flask import request
from flask.views import MethodView
from flask_login import current_user, login_required
from marshmallow import ValidationError

from tuned.apis.admin.schemas.blogs import (
    AdminApproveCommentSchema,
    AdminCreateBlogCategorySchema,
    AdminUpdateBlogCategorySchema,
)
from tuned.core.logging import get_logger
from tuned.dtos import BlogCategoryDTO
from tuned.extensions import db
from tuned.interface.admin.blogs import AdminBlogService
from tuned.repository import Repository
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound
from tuned.utils.dependencies import get_services
from tuned.utils.decorators import admin_required
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
# Categories
# ─────────────────────────────────────────────────────────────────────────────

class AdminBlogCategoriesListView(MethodView):
    """
    GET  /admin/blogs/categories  → list all categories with post counts
    POST /admin/blogs/categories  → create a new category
    """
    decorators = [login_required, admin_required]

    def get(self):
        try:
            categories = _admin_blog_service().list_categories_with_count()
            return success_response(data=[asdict(c) for c in categories])
        except DatabaseError as exc:
            logger.error("[AdminBlogCategoriesList.get] %r", exc)
            return error_response("Failed to fetch categories", status=500)
        except Exception as exc:
            logger.error("[AdminBlogCategoriesList.get] %r", exc)
            return error_response("Internal server error", status=500)

    def post(self):
        try:
            validated = AdminCreateBlogCategorySchema().load(request.get_json() or {})
            from tuned.models import BlogCategory
            from tuned.models.utils import generate_slug
            slug = generate_slug(validated["name"], BlogCategory, db.session)
            dto = BlogCategoryDTO(
                name=validated["name"],
                slug=slug,
                description=validated.get("description", ""),
                created_by=str(current_user.id),
            )
            result = _admin_blog_service().create_category(
                dto,
                actor_id=str(current_user.id),
                ip_address=request.remote_addr or "system",
                user_agent=request.headers.get("User-Agent", "system"),
            )
            return created_response(data=asdict(result))
        except ValidationError as err:
            return validation_error_response(err.messages)
        except AlreadyExists:
            return error_response("A category with this name already exists", status=409)
        except DatabaseError as exc:
            logger.error("[AdminBlogCategoriesList.post] %r", exc)
            return error_response("Failed to create category", status=500)
        except Exception as exc:
            logger.error("[AdminBlogCategoriesList.post] %r", exc)
            return error_response("Internal server error", status=500)


class AdminBlogCategoryDetailView(MethodView):
    """
    PATCH  /admin/blogs/categories/<category_id>  → update category
    DELETE /admin/blogs/categories/<category_id>  → soft-delete category
    """
    decorators = [login_required, admin_required]

    def patch(self, category_id: str):
        try:
            validated = AdminUpdateBlogCategorySchema().load(request.get_json() or {})
            dto = BlogCategoryDTO(
                name=validated.get("name", ""),
                slug="",
                description=validated.get("description", ""),
                updated_by=str(current_user.id),
            )
            result = _admin_blog_service().update_category(
                category_id, dto,
                actor_id=str(current_user.id),
                ip_address=request.remote_addr or "system",
                user_agent=request.headers.get("User-Agent", "system"),
            )
            return success_response(data=asdict(result))
        except ValidationError as err:
            return validation_error_response(err.messages)
        except NotFound:
            return error_response("Category not found", status=404)
        except DatabaseError as exc:
            logger.error("[AdminBlogCategoryDetail.patch] %r", exc)
            return error_response("Failed to update category", status=500)
        except Exception as exc:
            logger.error("[AdminBlogCategoryDetail.patch] %r", exc)
            return error_response("Internal server error", status=500)

    def delete(self, category_id: str):
        try:
            _admin_blog_service().delete_category(
                category_id,
                actor_id=str(current_user.id),
                ip_address=request.remote_addr or "system",
                user_agent=request.headers.get("User-Agent", "system"),
            )
            return no_content_response()
        except NotFound:
            return error_response("Category not found", status=404)
        except Exception as exc:
            logger.error("[AdminBlogCategoryDetail.delete] %r", exc)
            return error_response("Failed to delete category", status=500)


# ─────────────────────────────────────────────────────────────────────────────
# Comments
# ─────────────────────────────────────────────────────────────────────────────

class AdminBlogCommentApproveView(MethodView):
    """PATCH /admin/blogs/comments/<comment_id>/approve."""
    decorators = [login_required, admin_required]

    def patch(self, comment_id: str):
        try:
            validated = AdminApproveCommentSchema().load(request.get_json() or {})
            result = _admin_blog_service().approve_comment(
                comment_id,
                approved=validated["approved"],
                actor_id=str(current_user.id),
                ip_address=request.remote_addr or "system",
                user_agent=request.headers.get("User-Agent", "system"),
            )
            return success_response(data=asdict(result))
        except ValidationError as err:
            return validation_error_response(err.messages)
        except NotFound:
            return error_response("Comment not found", status=404)
        except Exception as exc:
            logger.error("[AdminBlogCommentApprove.patch] %r", exc)
            return error_response("Failed to update comment status", status=500)


class AdminBlogCommentDetailView(MethodView):
    """DELETE /admin/blogs/comments/<comment_id> – soft-delete a comment."""
    decorators = [login_required, admin_required]

    def delete(self, comment_id: str):
        try:
            _admin_blog_service().delete_comment(
                comment_id,
                actor_id=str(current_user.id),
                ip_address=request.remote_addr or "system",
                user_agent=request.headers.get("User-Agent", "system"),
            )
            return no_content_response()
        except NotFound:
            return error_response("Comment not found", status=404)
        except Exception as exc:
            logger.error("[AdminBlogCommentDetail.delete] %r", exc)
            return error_response("Failed to delete comment", status=500)


# ─────────────────────────────────────────────────────────────────────────────
# Reactions
# ─────────────────────────────────────────────────────────────────────────────

class AdminBlogReactionDetailView(MethodView):
    """DELETE /admin/blogs/reactions/<reaction_id> – soft-delete a reaction."""
    decorators = [login_required, admin_required]

    def delete(self, reaction_id: str):
        try:
            _admin_blog_service().delete_reaction(
                reaction_id,
                actor_id=str(current_user.id),
                ip_address=request.remote_addr or "system",
                user_agent=request.headers.get("User-Agent", "system"),
            )
            return no_content_response()
        except NotFound:
            return error_response("Reaction not found", status=404)
        except Exception as exc:
            logger.error("[AdminBlogReactionDetail.delete] %r", exc)
            return error_response("Failed to delete reaction", status=500)
