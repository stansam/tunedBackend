from typing import List, Any
import logging
from tuned.core.logging import get_logger
from tuned.dtos import SearchResponseDTO, SearchCountsDTO, SearchResultItemDTO
from tuned.repository import Repository

logger: logging.Logger = get_logger(__name__)

class SearchService:
    def __init__(self, repos: Repository) -> None:
        self._repos = repos

    def global_search(self, query: str, search_type: str = 'all', page: int = 1, per_page: int = 20) -> SearchResponseDTO:
        clean_query = query.strip()
        escaped_query = clean_query.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        search_pattern = f"%{escaped_query}%"
        
        offset = (page - 1) * per_page
        
        results: dict[str, List[SearchResultItemDTO]] = {
            'services': [],
            'samples': [],
            'blogs': [],
            'faqs': [],
            'tags': []
        }
        
        counts = SearchCountsDTO()

        # Search services
        if search_type in ['all', 'service']:
            services = self._repos.search.search_services(search_pattern, offset, per_page)
            results['services'] = [
                SearchResultItemDTO(
                    id=str(s.id),
                    type='service',
                    title=s.name,
                    slug=s.slug,
                    description=s.description,
                    category=s.category.name if s.category else None
                )
                for s in services
            ]
            counts.services = len(results['services'])

        # Search samples
        if search_type in ['all', 'sample']:
            samples = self._repos.search.search_samples(search_pattern, offset, per_page)
            results['samples'] = [
                SearchResultItemDTO(
                    id=str(s.id),
                    type='sample',
                    title=s.title,
                    slug=s.slug,
                    description=s.excerpt,
                    service=s.service.name if s.service else None
                )
                for s in samples
            ]
            counts.samples = len(results['samples'])

        # Search blogs
        if search_type in ['all', 'blog']:
            blogs = self._repos.search.search_blogs(search_pattern, offset, per_page)
            results['blogs'] = [
                SearchResultItemDTO(
                    id=str(b.id),
                    type='blog',
                    title=b.title,
                    slug=b.slug,
                    description=b.excerpt,
                    category=b.category.name if b.category else None,
                    published_at=b.published_at.isoformat() if b.published_at else None
                )
                for b in blogs
            ]
            counts.blogs = len(results['blogs'])

        # Search FAQs
        if search_type in ['all', 'faq']:
            faqs = self._repos.search.search_faqs(search_pattern, offset, per_page)
            results['faqs'] = [
                SearchResultItemDTO(
                    id=str(f.id),
                    type='faq',
                    title=f.question,
                    question=f.question,
                    answer=f.answer,
                    category=f.category
                )
                for f in faqs
            ]
            counts.faqs = len(results['faqs'])

        # Search tags
        if search_type in ['all', 'tag']:
            tags = self._repos.search.search_tags(search_pattern, offset, per_page)
            results['tags'] = [
                SearchResultItemDTO(
                    id=str(t.id),
                    type='tag',
                    title=t.name,
                    slug=t.slug,
                    usage_count=t.usage_count
                )
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
