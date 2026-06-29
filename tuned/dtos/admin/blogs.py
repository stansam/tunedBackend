from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from tuned.models.blog import BlogCategory


@dataclass
class AdminBlogStatsDTO:
    """KPI stats returned by GET /admin/blogs/stats."""
    total_posts: int
    published_posts: int
    draft_posts: int
    total_comments: int
    pending_comments: int
    approved_comments: int
    total_categories: int
    total_reactions: int


@dataclass
class AdminBlogCategoryWithCountDTO:
    """Category DTO extended with post_count for admin listing."""
    id: str
    name: str
    slug: str
    description: Optional[str]
    post_count: int

    @classmethod
    def from_row(cls, row: tuple) -> "AdminBlogCategoryWithCountDTO":
        """Construct from a SQLAlchemy result row (category, count)."""
        category, post_count = row
        return cls(
            id=str(category.id),
            name=category.name,
            slug=category.slug,
            description=category.description,
            post_count=int(post_count),
        )
