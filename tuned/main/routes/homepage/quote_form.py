"""
Quote form options endpoint.

GET /api/quote-form/options - Get all options for populating quote form dropdowns
"""
from flask import jsonify
from tuned.main import main_bp
from tuned.models.service import Service, ServiceCategory, AcademicLevel, Deadline
from tuned.models.price import PricingCategory
from tuned.utils.responses import success_response, error_response
from tuned.redis_client import redis_client
import json
import logging

logger = logging.getLogger(__name__)

CACHE_KEY = 'quote_form:options'
CACHE_TTL = 600  # 10 minutes


@main_bp.route('/api/quote-form/options', methods=['GET'])
def get_quote_form_options():
    """
    Get all dropdown options for quote form.
    
    Returns services (grouped by category), academic levels,
    deadlines, and pricing categories.
    Cached for 10 minutes using Redis.
    
    Returns:
        JSON response with form options
    """
    try:
        # Try to get from cache first
        cached_data = redis_client.get(CACHE_KEY)
        if cached_data:
            logger.debug('Returning quote form options from cache')
            return success_response(json.loads(cached_data))
        
        # Fetch all active services with their categories
        services = Service.query.filter_by(is_active=True).order_by(Service.name).all()
        
        # Group services by category
        services_by_category = {}
        for service in services:
            category_name = service.category.name if service.category else 'Uncategorized'
            if category_name not in services_by_category:
                services_by_category[category_name] = []
            services_by_category[category_name].append({
                'id': service.id,
                'name': service.name,
                'pricing_category_id': service.pricing_category_id
            })
        
        # Fetch academic levels (sorted by order)
        academic_levels = AcademicLevel.query.order_by(AcademicLevel.order).all()
        
        # Fetch deadlines (sorted by order/hours)
        deadlines = Deadline.query.order_by(Deadline.order).all()
        
        # Fetch pricing categories
        pricing_categories = PricingCategory.query.order_by(
            PricingCategory.display_order
        ).all()
        
        # Serialize data
        data = {
            'services': services_by_category,
            'academic_levels': [
                {
                    'id': level.id,
                    'name': level.name,
                    'order': level.order
                }
                for level in academic_levels
            ],
            'deadlines': [
                {
                    'id': deadline.id,
                    'name': deadline.name,
                    'hours': deadline.hours,
                    'order': deadline.order
                }
                for deadline in deadlines
            ],
            'pricing_categories': [
                {
                    'id': cat.id,
                    'name': cat.name,
                    'description': cat.description,
                    'display_order': cat.display_order
                }
                for cat in pricing_categories
            ]
        }
        
        # Cache the result
        redis_client.setex(
            CACHE_KEY,
            CACHE_TTL,
            json.dumps(data)
        )
        
        logger.info('Quote form options fetched and cached successfully')
        return success_response(data)
        
    except Exception as e:
        logger.error(f'Error fetching quote form options: {str(e)}')
        return error_response(
            'Failed to fetch form options',
            status=500
        )
