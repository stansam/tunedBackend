"""
Global search endpoint.

GET /api/search - Search across services, samples, blogs, FAQs, and tags
"""
from flask import request
from sqlalchemy import or_
from tuned.main import main_bp
from tuned.main.schemas import SearchQuerySchema
from tuned.models.service import Service, ServiceCategory
from tuned.models.content import Sample, FAQ
from tuned.models.blog import BlogPost, BlogCategory
from tuned.models.tag import Tag
from tuned.utils.responses import (
    success_response, 
    error_response, 
    validation_error_response,
    paginated_response
)
from marshmallow import ValidationError
import logging

logger = logging.getLogger(__name__)


@main_bp.route('/api/search', methods=['GET'])
def global_search():
    """
    Global search across multiple models.
    
    Query parameters:
        - q: Search query (required)
        - type: Filter by type (all, service, sample, blog, faq, tag)
        - page: Page number (default: 1)
        - per_page: Items per page (default: 20, max: 100)
    
    Returns:
        JSON response with paginated search results grouped by type
    """
    try:
        # Validate query parameters
        schema = SearchQuerySchema()
        params = schema.load(request.args)
        
    except ValidationError as err:
        return validation_error_response(err.messages)
    
    try:
        query = params['q']
        search_type = params.get('type', 'all')
        page = params.get('page', 1)
        per_page = params.get('per_page', 20)
        
        # Build case-insensitive search pattern
        search_pattern = f'%{query}%'
        
        results = {
            'services': [],
            'samples': [],
            'blogs': [],
            'faqs': [],
            'tags': []
        }
        
        # Search services
        if search_type in ['all', 'service']:
            services = Service.query.filter(
                Service.is_active == True,
                or_(
                    Service.name.ilike(search_pattern),
                    Service.description.ilike(search_pattern)
                )
            ).limit(20).all()
            
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
        
        # Search samples
        if search_type in ['all', 'sample']:
            samples = Sample.query.filter(
                or_(
                    Sample.title.ilike(search_pattern),
                    Sample.excerpt.ilike(search_pattern),
                    Sample.content.ilike(search_pattern)
                )
            ).limit(20).all()
            
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
        
        # Search blogs
        if search_type in ['all', 'blog']:
            blogs = BlogPost.query.filter(
                BlogPost.is_published == True,
                or_(
                    BlogPost.title.ilike(search_pattern),
                    BlogPost.excerpt.ilike(search_pattern),
                    BlogPost.content.ilike(search_pattern)
                )
            ).limit(20).all()
            
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
        
        # Search FAQs
        if search_type in ['all', 'faq']:
            faqs = FAQ.query.filter(
                or_(
                    FAQ.question.ilike(search_pattern),
                    FAQ.answer.ilike(search_pattern)
                )
            ).limit(20).all()
            
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
        
        # Search tags
        if search_type in ['all', 'tag']:
            tags = Tag.query.filter(
                Tag.name.ilike(search_pattern)
            ).limit(20).all()
            
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
        
        # Calculate total results
        total_results = sum(len(results[key]) for key in results)
        
        # Add result counts to response
        response_data = {
            'query': query,
            'type': search_type,
            'results': results,
            'counts': {
                'services': len(results['services']),
                'samples': len(results['samples']),
                'blogs': len(results['blogs']),
                'faqs': len(results['faqs']),
                'tags': len(results['tags']),
                'total': total_results
            }
        }
        
        logger.info(f'Search query "{query}" returned {total_results} results')
        return success_response(response_data)
        
    except Exception as e:
        logger.error(f'Error performing search: {str(e)}')
        return error_response(
            'Failed to perform search',
            status=500
        )
