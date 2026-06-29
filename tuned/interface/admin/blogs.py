from __future__ import annotations

import logging
from dataclasses import asdict
from datetime import datetime, timezone
from typing import List, Optional, TYPE_CHECKING

from tuned.core.logging import get_logger
from tuned.dtos import (
    BlogCategoryDTO,
    BlogCategoryResponseDTO,
    BlogPostDTO,
    BlogPostResponseDTO,
    BlogPostListRequestDTO,
    BlogPostListResponseDTO,
    BlogCommentDTO,
    BlogCommentResponseDTO,
    CommentReactionDTO,
    CommentReactionResponseDTO,
)
from tuned.dtos.admin.blogs import AdminBlogStatsDTO, AdminBlogCategoryWithCountDTO
from tuned.models.blog import BlogPost, BlogComment, BlogCategory, CommentReaction
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound

if TYPE_CHECKING:
    from tuned.repository import Repository
    from tuned.interface import Services

logger: logging.Logger = get_logger(__name__)


class AdminBlogService:
    """Orchestration service for admin-protected blog operations.

    Wraps the domain-level blog interface services (BlogCategoryService,
    BlogPostService, BlogCommentService, CommentReactionService) and adds:
      - Admin-scoped statistics (KPI endpoint)
      - Admin-scoped category listing with post counts
      - Admin-scoped post listing (drafts + published)
      - Socket.IO event emission via the blog EventBus events
    """

    def __init__(self, repos: "Repository", services: "Services") -> None:
        self._repos = repos
        self._services = services

    # ------------------------------------------------------------------ #
    # Stats                                                                #
    # ------------------------------------------------------------------ #

    def get_stats(self) -> AdminBlogStatsDTO:
        """Aggregate KPI counts across all blog entities."""
        try:
            from sqlalchemy import func, select
            session = self._repos.session

            total_posts: int = session.execute(
                select(func.count(BlogPost.id))
            ).scalar() or 0

            published_posts: int = session.execute(
                select(func.count(BlogPost.id)).where(BlogPost.is_published == True)
            ).scalar() or 0

            draft_posts: int = total_posts - published_posts

            total_categories: int = session.execute(
                select(func.count(BlogCategory.id))
            ).scalar() or 0

            total_comments: int = session.execute(
                select(func.count(BlogComment.id))
            ).scalar() or 0

            pending_comments: int = session.execute(
                select(func.count(BlogComment.id)).where(BlogComment.approved == False)
            ).scalar() or 0

            approved_comments: int = total_comments - pending_comments

            total_reactions: int = session.execute(
                select(func.count(CommentReaction.id))
            ).scalar() or 0

            return AdminBlogStatsDTO(
                total_posts=total_posts,
                published_posts=published_posts,
                draft_posts=draft_posts,
                total_comments=total_comments,
                pending_comments=pending_comments,
                approved_comments=approved_comments,
                total_categories=total_categories,
                total_reactions=total_reactions,
            )
        except Exception as exc:
            logger.error("[AdminBlogService.get_stats] %r", exc)
            raise DatabaseError("Failed to aggregate blog statistics")

    # ------------------------------------------------------------------ #
    # Categories                                                           #
    # ------------------------------------------------------------------ #

    def list_categories_with_count(self) -> List[AdminBlogCategoryWithCountDTO]:
        """Admin-only: returns all blog categories with post counts."""
        try:
            rows = self._repos.blog.list_blog_categories_with_count()
            return [AdminBlogCategoryWithCountDTO.from_row(row) for row in rows]
        except DatabaseError:
            raise
        except Exception as exc:
            logger.error("[AdminBlogService.list_categories_with_count] %r", exc)
            raise DatabaseError("Failed to list categories with counts")

    def create_category(
        self,
        data: BlogCategoryDTO,
        actor_id: Optional[str] = None,
        ip_address: str = "system",
        user_agent: str = "system",
    ) -> BlogCategoryResponseDTO:
        return self._services.blogs.category.create_category(
            data, actor_id=actor_id, ip_address=ip_address, user_agent=user_agent
        )

    def update_category(
        self,
        category_id: str,
        data: BlogCategoryDTO,
        actor_id: Optional[str] = None,
        ip_address: str = "system",
        user_agent: str = "system",
    ) -> BlogCategoryResponseDTO:
        return self._services.blogs.category.update_or_delete_category(
            category_id, data, actor_id=actor_id, ip_address=ip_address, user_agent=user_agent
        )

    def delete_category(
        self,
        category_id: str,
        actor_id: Optional[str] = None,
        ip_address: str = "system",
        user_agent: str = "system",
    ) -> BlogCategoryResponseDTO:
        delete_dto = BlogCategoryDTO(
            name="",
            slug="",
            description="",
            is_deleted=True,
            deleted_by=actor_id,
        )
        return self._services.blogs.category.update_or_delete_category(
            category_id, delete_dto, actor_id=actor_id, ip_address=ip_address, user_agent=user_agent
        )

    def list_posts(self, req: BlogPostListRequestDTO) -> BlogPostListResponseDTO:
        """Admin version: returns all posts regardless of published status."""
        try:
            return self._repos.blog.get_all_posts(req)
        except DatabaseError:
            raise
        except Exception as exc:
            logger.error("[AdminBlogService.list_posts] %r", exc)
            raise DatabaseError("Failed to list blog posts")

    def get_post_by_slug(self, slug: str) -> BlogPostResponseDTO:
        """Returns a single post by slug – bypasses any cache, returns any status."""
        return self._services.blogs.post.get_by_slug(slug)

    def create_post(
        self,
        data: BlogPostDTO,
        actor_id: Optional[str] = None,
        ip_address: str = "system",
        user_agent: str = "system",
    ) -> BlogPostResponseDTO:
        return self._services.blogs.post.create_post(
            data, actor_id=actor_id, ip_address=ip_address, user_agent=user_agent
        )

    def update_post(
        self,
        post_id: str,
        data: BlogPostDTO,
        actor_id: Optional[str] = None,
        ip_address: str = "system",
        user_agent: str = "system",
    ) -> BlogPostResponseDTO:
        return self._services.blogs.post.update_or_delete_post(
            post_id, data, actor_id=actor_id, ip_address=ip_address, user_agent=user_agent
        )

    def delete_post(
        self,
        post_id: str,
        actor_id: Optional[str] = None,
        ip_address: str = "system",
        user_agent: str = "system",
    ) -> BlogPostResponseDTO:
        delete_dto = BlogPostDTO(
            title="",
            content="",
            author="",
            category_id="",
            is_deleted=True,
            deleted_by=actor_id,
        )
        return self._services.blogs.post.update_or_delete_post(
            post_id, delete_dto, actor_id=actor_id, ip_address=ip_address, user_agent=user_agent
        )

    def toggle_publish(
        self,
        post_id: str,
        is_published: bool,
        actor_id: Optional[str] = None,
        ip_address: str = "system",
        user_agent: str = "system",
    ) -> BlogPostResponseDTO:
        """Atomically toggle the published status of a post."""
        update_dto = BlogPostDTO(
            title="",
            content="",
            author="",
            category_id="",
            is_published=is_published,
            published_at=datetime.now(timezone.utc) if is_published else None,
            updated_by=actor_id,
        )
        return self._services.blogs.post.update_or_delete_post(
            post_id, update_dto, actor_id=actor_id, ip_address=ip_address, user_agent=user_agent
        )

    def toggle_featured(
        self,
        post_id: str,
        is_featured: bool,
        actor_id: Optional[str] = None,
        ip_address: str = "system",
        user_agent: str = "system",
    ) -> BlogPostResponseDTO:
        """Atomically toggle the featured status of a post."""
        update_dto = BlogPostDTO(
            title="",
            content="",
            author="",
            category_id="",
            is_featured=is_featured,
            updated_by=actor_id,
        )
        return self._services.blogs.post.update_or_delete_post(
            post_id, update_dto, actor_id=actor_id, ip_address=ip_address, user_agent=user_agent
        )

    def get_post_comments(self, post_id: str) -> List[BlogCommentResponseDTO]:
        """Returns all comments for a post (approved AND pending)."""
        return self._services.blogs.comment.get_blog_comments(post_id)

    def approve_comment(
        self,
        comment_id: str,
        approved: bool,
        actor_id: Optional[str] = None,
        ip_address: str = "system",
        user_agent: str = "system",
    ) -> BlogCommentResponseDTO:
        """Set the approved flag on a comment."""
        update_dto = BlogCommentDTO(
            post_id="",
            content="",
            approved=approved,
            updated_by=actor_id,
        )
        return self._services.blogs.comment.update_or_delete_comment(
            comment_id, update_dto, actor_id=actor_id, ip_address=ip_address, user_agent=user_agent
        )

    def delete_comment(
        self,
        comment_id: str,
        actor_id: Optional[str] = None,
        ip_address: str = "system",
        user_agent: str = "system",
    ) -> BlogCommentResponseDTO:
        delete_dto = BlogCommentDTO(
            post_id="",
            content="",
            is_deleted=True,
            deleted_by=actor_id,
        )
        return self._services.blogs.comment.update_or_delete_comment(
            comment_id, delete_dto, actor_id=actor_id, ip_address=ip_address, user_agent=user_agent
        )

    def delete_reaction(
        self,
        reaction_id: str,
        actor_id: Optional[str] = None,
        ip_address: str = "system",
        user_agent: str = "system",
    ) -> CommentReactionResponseDTO:
        delete_dto = CommentReactionDTO(
            comment_id="",
            reaction_type="like",
            is_deleted=True,
            deleted_by=actor_id,
        )
        return self._services.blogs.reaction.update_or_delete_comment_reaction(
            reaction_id, delete_dto, ip_address=ip_address, user_agent=user_agent
        )
