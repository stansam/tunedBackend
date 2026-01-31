"""
Samples listing and detail endpoints.

GET /api/samples - List all samples with filtering
GET /api/samples/<slug> - Get sample details
"""
from flask import request
from sqlalchemy import or_, desc, asc
from tuned.main import main_bp
from tuned.main.schemas import SampleFilterSchema
from tuned.models.content import Sample
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


@main_bp.route('/api/samples', methods=['GET'])
def list_samples():
    """
    List all samples with filtering, search, and pagination.
    
    Query parameters:
        - service_id: Filter by service
        - featured: Filter by featured status
        - q: Search query (searches title, excerpt, content)
        - sort: Sort field (created_at, word_count, title)
        - order: Sort order (asc, desc)
        - page: Page number
        - per_page: Items per page
    
    Returns:
        JSON response with paginated samples
    """
    try:
        # Validate query parameters
        schema = SampleFilterSchema()
        params = schema.load(request.args)
        
    except ValidationError as err:
        return validation_error_response(err.messages)
    
    try:
        # Build query
        query = Sample.query
        
        # Filter by service
        if params.get('service_id'):
            query = query.filter_by(service_id=params['service_id'])
        
        # Filter by featured status
        if params.get('featured') is not None:
            query = query.filter_by(featured=params['featured'])
        
        # Search by title/excerpt/content
        if params.get('q'):
            search_pattern = f"%{params['q']}%"
            query = query.filter(
                or_(
                    Sample.title.ilike(search_pattern),
                    Sample.excerpt.ilike(search_pattern),
                    Sample.content.ilike(search_pattern)
                )
            )
        
        # Sorting
        sort_field = params.get('sort', 'created_at')
        sort_order = params.get('order', 'desc')
        
        if sort_field == 'created_at':
            query = query.order_by(
                asc(Sample.created_at) if sort_order == 'asc' else desc(Sample.created_at)
            )
        elif sort_field == 'word_count':
            query = query.order_by(
                asc(Sample.word_count) if sort_order == 'asc' else desc(Sample.word_count)
            )
        elif sort_field == 'title':
            query = query.order_by(
                asc(Sample.title) if sort_order == 'asc' else desc(Sample.title)
            )
        
        # Get total count
        total = query.count()
        
        # Paginate
        page = params.get('page', 1)
        per_page = params.get('per_page', 20)
        
        samples = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Serialize data
        items = [
            {
                'id': s.id,
                'title': s.title,
                'excerpt': s.excerpt,
                'slug': s.slug,
                'word_count': s.word_count,
                'featured': s.featured,
                'image': s.image,
                'created_at': s.created_at.isoformat() if s.created_at else None,
                'service': {
                    'id': s.service.id,
                    'name': s.service.name,
                    'slug': s.service.slug
                } if s.service else None
            }
            for s in samples.items
        ]
        
        logger.info(f'Samples listed: page {page}, total {total}')
        return paginated_response(
            items=items,
            page=page,
            per_page=per_page,
            total=total
        )
        
    except Exception as e:
        logger.error(f'Error listing samples: {str(e)}')
        return error_response(
            'Failed to fetch samples',
            status=500
        )


@main_bp.route('/api/samples/<slug>', methods=['GET'])
def get_sample_details(slug):
    """
    Get sample details by slug.
    
    Includes full content, service details, tags, and related samples.
    
    Args:
        slug: Sample slug
    
    Returns:
        JSON response with sample details
    """
    try:
        # Query sample
        sample = Sample.query.filter_by(slug=slug).first()
        
        if not sample:
            logger.warning(f'Sample not found: {slug}')
            return not_found_response('Sample not found')
        
        # Get related samples from same service (limit 3, exclude current)
        related_samples = []
        if sample.service:
            related = Sample.query.filter(
                Sample.service_id == sample.service_id,
                Sample.id != sample.id
            ).limit(3).all()
            
            related_samples = [
                {
                    'id': s.id,
                    'title': s.title,
                    'excerpt': s.excerpt,
                    'slug': s.slug,
                    'image': s.image
                }
                for s in related
            ]
        
        # Serialize data
        data = {
            'id': sample.id,
            'title': sample.title,
            'content': sample.content,
            'excerpt': sample.excerpt,
            'slug': sample.slug,
            'word_count': sample.word_count,
            'featured': sample.featured,
            'tags': sample.tags,
            'image': sample.image,
            'created_at': sample.created_at.isoformat() if sample.created_at else None,
            'service': {
                'id': sample.service.id,
                'name': sample.service.name,
                'slug': sample.service.slug,
                'description': sample.service.description
            } if sample.service else None,
            'related_samples': related_samples
        }
        
        logger.info(f'Sample details fetched: {slug}')
        return success_response(data)
        
    except Exception as e:
        logger.error(f'Error fetching sample details: {str(e)}')
        return error_response(
            'Failed to fetch sample details',
            status=500
        )
