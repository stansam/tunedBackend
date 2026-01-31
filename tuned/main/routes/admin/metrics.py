"""
Admin routes for analytics and metrics.

Provides endpoints for viewing application performance metrics.
"""
from flask import jsonify
from tuned.main import main_bp
from tuned.auth.decorators import jwt_required, require_admin
from tuned.utils.responses import success_response
from tuned.utils.metrics import metrics


@main_bp.route('/api/admin/metrics/endpoints', methods=['GET'])
@jwt_required
@require_admin
def get_endpoint_metrics():
    """Get metrics for all endpoints"""
    # Define key endpoints to track
    endpoints = [
        '/api/featured',
        '/api/services',
        '/api/samples',
        '/api/blogs',
        '/api/search',
        '/api/testimonials',
        '/api/newsletter/subscribe'
    ]
    
    all_metrics = {}
    for endpoint in endpoints:
        endpoint_data = metrics.get_endpoint_metrics(endpoint, days=7)
        if endpoint_data:
            all_metrics[endpoint] = endpoint_data
    
    return success_response(all_metrics)


@main_bp.route('/api/admin/metrics/cache', methods=['GET'])
@jwt_required
@require_admin
def get_cache_metrics():
    """Get cache performance metrics"""
    cache_data = metrics.get_cache_metrics(days=7)
    return success_response(cache_data)


@main_bp.route('/api/admin/metrics/search', methods=['GET'])
@jwt_required
@require_admin
def get_search_metrics():
    """Get search analytics"""
    search_data = metrics.get_search_analytics(days=7, top_n=20)
    return success_response(search_data)


@main_bp.route('/api/admin/metrics/summary', methods=['GET'])
@jwt_required
@require_admin
def get_metrics_summary():
    """Get summary of all metrics"""
    summary = {
        'cache': metrics.get_cache_metrics(days=1),  # Today only
        'search': metrics.get_search_analytics(days=1, top_n=10),
        'top_endpoints': {}
    }
    
    # Get today's top endpoints
    key_endpoints = ['/api/featured', '/api/services', '/api/blogs', '/api/search']
    for endpoint in key_endpoints:
        endpoint_data = metrics.get_endpoint_metrics(endpoint, days=1)
        if endpoint_data:
            summary['top_endpoints'][endpoint] = endpoint_data
    
    return success_response(summary)
