"""
Homepage featured content endpoint.

GET /api/featured - Fetch featured services, samples, and blog posts
"""
from flask import jsonify
from tuned.main import main_bp
from tuned.models.service import Service
from tuned.models.content import Sample
from tuned.models.blog import BlogPost
from tuned.utils.responses import success_response, error_response
from tuned.redis_client import redis_client
import json
import logging

logger = logging.getLogger(__name__)

CACHE_KEY = 'homepage:featured'
CACHE_TTL = 300  # 5 minutes


@main_bp.route('/api/featured', methods=['GET'])
def get_featured_content():
    """
    Get featured content for homepage.
    
    Returns featured services, samples, and blog posts.
    Cached for 5 minutes using Redis.
    
    Returns:
        JSON response with featured content
    """
    try:
        # Try to get from cache first
        cached_data = redis_client.get(CACHE_KEY)
        if cached_data:
            logger.debug('Returning featured content from cache')
            return success_response(json.loads(cached_data))
        
        # Query featured services (limit 6, active only)
        featured_services = Service.query.filter_by(
            featured=True,
            is_active=True
        ).limit(6).all()
        
        # Query featured samples (limit 6)
        featured_samples = Sample.query.filter_by(
            featured=True
        ).limit(6).all()
        
        # Query latest published blog posts (limit 6)
        latest_blogs = BlogPost.query.filter_by(
            is_published=True
        ).order_by(
            BlogPost.published_at.desc()
        ).limit(6).all()
        
        # Serialize data
        data = {
            'services': [
                {
                    'id': s.id,
                    'name': s.name,
                    'description': s.description,
                    'slug': s.slug,
                    'category': {
                        'id': s.category.id,
                        'name': s.category.name
                    } if s.category else None
                }
                for s in featured_services
            ],
            'samples': [
                {
                    'id': sample.id,
                    'title': sample.title,
                    'excerpt': sample.excerpt,
                    'slug': sample.slug,
                    'word_count': sample.word_count,
                    'image': sample.image,
                    'service': {
                        'id': sample.service.id,
                        'name': sample.service.name
                    } if sample.service else None
                }
                for sample in featured_samples
            ],
            'blogs': [
                {
                    'id': blog.id,
                    'title': blog.title,
                    'excerpt': blog.excerpt,
                    'slug': blog.slug,
                    'featured_image': blog.featured_image,
                    'author': blog.author,
                    'published_at': blog.published_at.isoformat() if blog.published_at else None,
                    'category': {
                        'id': blog.category.id,
                        'name': blog.category.name
                    } if blog.category else None
                }
                for blog in latest_blogs
            ]
        }
        
        # Cache the result
        redis_client.setex(
            CACHE_KEY,
            CACHE_TTL,
            json.dumps(data)
        )
        
        logger.info('Featured content fetched and cached successfully')
        return success_response(data)
        
    except Exception as e:
        logger.error(f'Error fetching featured content: {str(e)}')
        return error_response(
            'Failed to fetch featured content',
            status=500
        )
