from typing import List, Any
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, or_

from tuned.models import Service, Sample, BlogPost, FAQ, Tag
from tuned.repository.protocols.search import SearchRepositoryProtocol

class SearchRepository(SearchRepositoryProtocol):
    def __init__(self, session: Session) -> None:
        self.session = session

    def search_services(self, pattern: str, offset: int, limit: int) -> List[Service]:
        stmt = (
            select(Service)
            .options(selectinload(Service.category))
            .where(
                Service.is_active == True,
                or_(
                    Service.name.ilike(pattern, escape='\\'),
                    Service.description.ilike(pattern, escape='\\')
                )
            )
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(stmt).all())

    def search_samples(self, pattern: str, offset: int, limit: int) -> List[Sample]:
        stmt = (
            select(Sample)
            .options(selectinload(Sample.service))
            .where(
                or_(
                    Sample.title.ilike(pattern, escape='\\'),
                    Sample.excerpt.ilike(pattern, escape='\\'),
                    Sample.content.ilike(pattern, escape='\\')
                )
            )
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(stmt).all())

    def search_blogs(self, pattern: str, offset: int, limit: int) -> List[BlogPost]:
        stmt = (
            select(BlogPost)
            .options(selectinload(BlogPost.category))
            .where(
                BlogPost.is_published == True,
                or_(
                    BlogPost.title.ilike(pattern, escape='\\'),
                    BlogPost.excerpt.ilike(pattern, escape='\\'),
                    BlogPost.content.ilike(pattern, escape='\\')
                )
            )
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(stmt).all())

    def search_faqs(self, pattern: str, offset: int, limit: int) -> List[FAQ]:
        stmt = (
            select(FAQ)
            .where(
                or_(
                    FAQ.question.ilike(pattern, escape='\\'),
                    FAQ.answer.ilike(pattern, escape='\\')
                )
            )
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(stmt).all())

    def search_tags(self, pattern: str, offset: int, limit: int) -> List[Tag]:
        stmt = (
            select(Tag)
            .where(
                Tag.name.ilike(pattern, escape='\\')
            )
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(stmt).all())
