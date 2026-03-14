"""
Testimonials endpoint.

GET /api/testimonials - Get approved testimonials with pagination
"""
from flask import request
from tuned.main import main_bp
from tuned.models.content import Testimonial
from tuned.utils.responses import (
    success_response,
    error_response,
    paginated_response
)
from tuned.redis_client import redis_client
import json
import logging

logger = logging.getLogger(__name__)

CACHE_KEY_PREFIX = 'testimonials'
CACHE_TTL = 900  # 15 minutes


@main_bp.route('/api/testimonials', methods=['GET'])
def get_testimonials():
    """
    Get approved testimonials with pagination.
    
    Query parameters:
        - service_id: Filter by service (optional)
        - page: Page number (default: 1)
        - per_page: Items per page (default: 10, max: 50)
    
    Returns:
        JSON response with paginated testimonials
    """
    try:
        # Get query parameters
        service_id = request.args.get('service_id', type=int)
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 50)
        
        # Build cache key
        cache_key = f'{CACHE_KEY_PREFIX}:service_{service_id}:page_{page}:per_{per_page}'
        
        # Try to get from cache
        cached_data = redis_client.get(cache_key)
        if cached_data:
            logger.debug(f'Returning testimonials from cache: {cache_key}')
            cached = json.loads(cached_data)
            return paginated_response(
                items=cached['items'],
                page=cached['page'],
                per_page=cached['per_page'],
                total=cached['total']
            )
        
        # Build query
        query = Testimonial.query.filter_by(is_approved=True)
        
        # Filter by service if provided
        if service_id:
            query = query.filter_by(service_id=service_id)
        
        # Order by created_at descending
        query = query.order_by(Testimonial.created_at.desc())
        
        # Get total count
        total = query.count()
        
        # Paginate
        testimonials = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Serialize data
        items = [
            {
                'id': t.id,
                'content': t.content,
                'rating': t.rating,
                'created_at': t.created_at.isoformat() if t.created_at else None,
                'user': {
                    'id': t.author.id,
                    'name': t.author.get_name(),
                    'profile_pic': t.author.profile_pic
                } if t.author else None,
                'service': {
                    'id': t.service.id,
                    'name': t.service.name
                } if t.service else None,
                'order_id': t.order_id
            }
            for t in testimonials.items
        ]
        
        # Cache the result
        cache_data = {
            'items': items,
            'page': page,
            'per_page': per_page,
            'total': total
        }
        redis_client.setex(
            cache_key,
            CACHE_TTL,
            json.dumps(cache_data)
        )
        
        logger.info(f'Testimonials fetched: page {page}, total {total}')
        return paginated_response(
            items=items,
            page=page,
            per_page=per_page,
            total=total
        )
        
    except Exception as e:
        logger.error(f'Error fetching testimonials: {str(e)}')
        return error_response(
            'Failed to fetch testimonials',
            status=500
        )
