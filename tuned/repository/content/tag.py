from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from tuned.models.tag import Tag
from typing import List

class TagRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_tags(self, limit: int = 20) -> List[Tag]:
        stmt = select(Tag).order_by(desc(Tag.usage_count)).limit(limit)
        return list(self.session.scalars(stmt).all())

    def get_tag_by_slug(self, slug: str) -> Tag | None:
        stmt = select(Tag).where(Tag.slug == slug)
        return self.session.scalars(stmt).first()
