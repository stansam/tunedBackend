"""
Services listing and detail endpoints.

GET /api/services - List all services with filtering
GET /api/services/<slug> - Get service details
"""
from flask import request
from sqlalchemy import or_, desc, asc
from tuned.main import main_bp
from tuned.main.schemas import ServiceFilterSchema
from tuned.models.service import Service
from tuned.utils.responses import (
    success_response,
    error_response,
    not_found_response,
    validation_error_response,
    paginated_response
)
from tuned.redis_client import redis_client
from marshmallow import ValidationError
import json
import logging

logger = logging.getLogger(__name__)

CACHE_TTL = 600  # 10 minutes


@main_bp.route('/api/services', methods=['GET'])
def list_services():
    """
    List all services with filtering, search, and pagination.
    
    Query parameters:
        - category_id: Filter by category
        - featured: Filter by featured status
        - is_active: Filter by active status (default: true)
        - q: Search query (searches name and description)
        - sort: Sort field (name, created_at, category)
        - order: Sort order (asc, desc)
        - page: Page number
        - per_page: Items per page
    
    Returns:
        JSON response with paginated services
    """
    try:
        # Validate query parameters
        schema = ServiceFilterSchema()
        params = schema.load(request.args)
        
    except ValidationError as err:
        return validation_error_response(err.messages)
    
    try:
        # Build query
        query = Service.query
        
        # Filter by active status
        if params.get('is_active') is not None:
            query = query.filter_by(is_active=params['is_active'])
        
        # Filter by category
        if params.get('category_id'):
            query = query.filter_by(category_id=params['category_id'])
        
        # Filter by featured status
        if params.get('featured') is not None:
            query = query.filter_by(featured=params['featured'])
        
        # Search by name/description
        if params.get('q'):
            search_pattern = f"%{params['q']}%"
            query = query.filter(
                or_(
                    Service.name.ilike(search_pattern),
                    Service.description.ilike(search_pattern)
                )
            )
        
        # Sorting
        sort_field = params.get('sort', 'name')
        sort_order = params.get('order', 'asc')
        
        if sort_field == 'name':
            query = query.order_by(asc(Service.name) if sort_order == 'asc' else desc(Service.name))
        elif sort_field == 'created_at':
            query = query.order_by(asc(Service.id) if sort_order == 'asc' else desc(Service.id))
        elif sort_field == 'category':
            query = query.join(Service.category).order_by(
                asc('service_category.name') if sort_order == 'asc' else desc('service_category.name')
            )
        
        # Get total count
        total = query.count()
        
        # Paginate
        page = params.get('page', 1)
        per_page = params.get('per_page', 20)
        
        services = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Serialize data
        items = [
            {
                'id': s.id,
                'name': s.name,
                'description': s.description,
                'slug': s.slug,
                'featured': s.featured,
                'category': {
                    'id': s.category.id,
                    'name': s.category.name,
                    'description': s.category.description
                } if s.category else None,
                'pricing_category_id': s.pricing_category_id
            }
            for s in services.items
        ]
        
        logger.info(f'Services listed: page {page}, total {total}')
        return paginated_response(
            items=items,
            page=page,
            per_page=per_page,
            total=total
        )
        
    except Exception as e:
        logger.error(f'Error listing services: {str(e)}')
        return error_response(
            'Failed to fetch services',
            status=500
        )


@main_bp.route('/api/services/<slug>', methods=['GET'])
def get_service_details(slug):
    """
    Get service details by slug.
    
    Includes related samples and full category information.
    Cached for 10 minutes.
    
    Args:
        slug: Service slug
    
    Returns:
        JSON response with service details
    """
    try:
        # Build cache key
        cache_key = f'service:slug:{slug}'
        
        # Try to get from cache
        cached_data = redis_client.get(cache_key)
        if cached_data:
            logger.debug(f'Returning service from cache: {slug}')
            return success_response(json.loads(cached_data))
        
        # Query service
        service = Service.query.filter_by(slug=slug, is_active=True).first()
        
        if not service:
            logger.warning(f'Service not found: {slug}')
            return not_found_response('Service not found')
        
        # Get related samples (limit 3)
        related_samples = []
        if service.samples:
            related_samples = [
                {
                    'id': sample.id,
                    'title': sample.title,
                    'excerpt': sample.excerpt,
                    'slug': sample.slug,
                    'image': sample.image
                }
                for sample in service.samples[:3]
            ]
        
        # Serialize data
        data = {
            'id': service.id,
            'name': service.name,
            'description': service.description,
            'slug': service.slug,
            'featured': service.featured,
            'tags': service.tags,
            'category': {
                'id': service.category.id,
                'name': service.category.name,
                'description': service.category.description
            } if service.category else None,
            'pricing_category': {
                'id': service.pricing_category.id,
                'name': service.pricing_category.name,
                'description': service.pricing_category.description
            } if service.pricing_category else None,
            'related_samples': related_samples
        }
        
        # Cache the result
        redis_client.setex(
            cache_key,
            CACHE_TTL,
            json.dumps(data)
        )
        
        logger.info(f'Service details fetched: {slug}')
        return success_response(data)
        
    except Exception as e:
        logger.error(f'Error fetching service details: {str(e)}')
        return error_response(
            'Failed to fetch service details',
            status=500
        )
