from typing import List, Any
import logging
from tuned.core.logging import get_logger
from tuned.dtos import SearchResponseDTO, SearchCountsDTO
from tuned.repository import Repository

logger :logging.Logger = get_logger(__name__)

class SearchService:
    def __init__(self, repos: Repository) -> None:
        self._repos = repos

    def global_search(self, query: str, search_type: str = 'all', page: int = 1, per_page: int = 20) -> SearchResponseDTO:
        search_pattern = f"%{query}%"
        results: dict[str, List[dict[str, Any]]] = {
            'services': [],
            'samples': [],
            'blogs': [],
            'faqs': [],
            'tags': []
        }
        
        counts = SearchCountsDTO()

        # Search services
        if search_type in ['all', 'service']:
            from sqlalchemy import select, or_
            from tuned.models import Service
            stmt = select(Service).where(
                Service.is_active == True,
                or_(
                    Service.name.ilike(search_pattern),
                    Service.description.ilike(search_pattern)
                )
            ).limit(20)
            services = self._repos.service.session.scalars(stmt).all()
            results['services'] = [
                {
                    'id': s.id,
                    'name': s.name,
                    'description': s.description,
                    'slug': s.slug,
                    'type': 'service',
                    'category': s.category.name if s.category else None
                }
                for s in services
            ]
            counts.services = len(results['services'])

        # Search samples
        if search_type in ['all', 'sample']:
            from sqlalchemy import select, or_
            from tuned.models import Sample
            stmt = select(Sample).where(
                or_(
                    Sample.title.ilike(search_pattern),
                    Sample.excerpt.ilike(search_pattern),
                    Sample.content.ilike(search_pattern)
                )
            ).limit(20)
            samples = self._repos.sample.session.scalars(stmt).all()
            results['samples'] = [
                {
                    'id': s.id,
                    'title': s.title,
                    'excerpt': s.excerpt,
                    'slug': s.slug,
                    'type': 'sample',
                    'service': s.service.name if s.service else None
                }
                for s in samples
            ]
            counts.samples = len(results['samples'])

        # Search blogs
        if search_type in ['all', 'blog']:
            from sqlalchemy import select, or_
            from tuned.models import BlogPost
            stmt = select(BlogPost).where(
                BlogPost.is_published == True,
                or_(
                    BlogPost.title.ilike(search_pattern),
                    BlogPost.excerpt.ilike(search_pattern),
                    BlogPost.content.ilike(search_pattern)
                )
            ).limit(20)
            blogs = self._repos.blog.session.scalars(stmt).all()
            results['blogs'] = [
                {
                    'id': b.id,
                    'title': b.title,
                    'excerpt': b.excerpt,
                    'slug': b.slug,
                    'type': 'blog',
                    'category': b.category.name if b.category else None,
                    'published_at': b.published_at.isoformat() if b.published_at else None
                }
                for b in blogs
            ]
            counts.blogs = len(results['blogs'])

        # Search FAQs
        if search_type in ['all', 'faq']:
            from sqlalchemy import select, or_
            from tuned.models import FAQ
            stmt = select(FAQ).where(
                or_(
                    FAQ.question.ilike(search_pattern),
                    FAQ.answer.ilike(search_pattern)
                )
            ).limit(20)
            faqs = self._repos.faq.session.scalars(stmt).all()
            results['faqs'] = [
                {
                    'id': f.id,
                    'question': f.question,
                    'answer': f.answer,
                    'type': 'faq',
                    'category': f.category
                }
                for f in faqs
            ]
            counts.faqs = len(results['faqs'])

        # Search tags
        if search_type in ['all', 'tag']:
            from sqlalchemy import select
            from tuned.models import Tag
            stmt = select(Tag).where(
                Tag.name.ilike(search_pattern)
            ).limit(20)
            tags = self._repos.tag.session.scalars(stmt).all()
            results['tags'] = [
                {
                    'id': t.id,
                    'name': t.name,
                    'slug': t.slug,
                    'type': 'tag',
                    'usage_count': t.usage_count
                }
                for t in tags
            ]
            counts.tags = len(results['tags'])

        counts.total = sum([counts.services, counts.samples, counts.blogs, counts.faqs, counts.tags])
        
        return SearchResponseDTO(
            query=query,
            type=search_type,
            results=results,
            counts=counts
        )
