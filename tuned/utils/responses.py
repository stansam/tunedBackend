"""
Standardized API response utilities.

Provides consistent JSON response formats across all API endpoints.
All responses follow a standard structure for better frontend integration.
"""
from flask import jsonify
from typing import Any, Dict, Optional, List


def success_response(
    data: Any = None,
    message: Optional[str] = None,
    status: int = 200
) -> tuple:
    """
    Create a standardized success response.
    
    Args:
        data: Response data (can be dict, list, or any JSON-serializable type)
        message: Optional success message
        status: HTTP status code (default: 200)
        
    Returns:
        tuple: (response_dict, status_code)
        
    Example:
        return success_response({'user': user_data}, 'Login successful', 200)
    """
    response = {
        'success': True,
        'data': data
    }
    
    if message:
        response['message'] = message
        
    return jsonify(response), status


def error_response(
    message: str,
    errors: Optional[Dict[str, List[str]]] = None,
    status: int = 400
) -> tuple:
    """
    Create a standardized error response.
    
    Args:
        message: Error message
        errors: Optional dict of field-specific errors (validation errors)
        status: HTTP status code (default: 400)
        
    Returns:
        tuple: (response_dict, status_code)
        
    Example:
        return error_response(
            'Validation failed',
            {'email': ['Email already exists']},
            400
        )
    """
    response = {
        'success': False,
        'message': message
    }
    
    if errors:
        response['errors'] = errors
        
    return jsonify(response), status


def validation_error_response(errors: Dict[str, List[str]]) -> tuple:
    """
    Create a standardized validation error response.
    
    Args:
        errors: Dict of field-specific validation errors
        
    Returns:
        tuple: (response_dict, status_code)
        
    Example:
        return validation_error_response({
            'email': ['Invalid email format'],
            'password': ['Password too weak']
        })
    """
    return error_response(
        message='Validation failed',
        errors=errors,
        status=422
    )


def paginated_response(
    items: list,
    page: int,
    per_page: int,
    total: int,
    message: Optional[str] = None
) -> tuple:
    """
    Create a standardized paginated response.
    
    Args:
        items: List of items for current page
        page: Current page number (1-indexed)
        per_page: Items per page
        total: Total number of items across all pages
        message: Optional message
        
    Returns:
        tuple: (response_dict, status_code)
        
    Example:
        return paginated_response(users, page=1, per_page=10, total=100)
    """
    import math
    
    total_pages = math.ceil(total / per_page) if per_page > 0 else 0
    
    response = {
        'success': True,
        'data': items,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    }
    
    if message:
        response['message'] = message
        
    return jsonify(response), 200


def created_response(data: Any, message: str = 'Resource created successfully') -> tuple:
    """
    Convenience function for 201 Created responses.
    
    Args:
        data: Created resource data
        message: Success message
        
    Returns:
        tuple: (response_dict, 201)
    """
    return success_response(data, message, 201)


def no_content_response() -> tuple:
    """
    Convenience function for 204 No Content responses.
    
    Returns:
        tuple: (empty response, 204)
    """
    return '', 204


def unauthorized_response(message: str = 'Unauthorized') -> tuple:
    """
    Convenience function for 401 Unauthorized responses.
    
    Args:
        message: Error message
        
    Returns:
        tuple: (response_dict, 401)
    """
    return error_response(message, status=401)


def forbidden_response(message: str = 'Forbidden') -> tuple:
    """
    Convenience function for 403 Forbidden responses.
    
    Args:
        message: Error message
        
    Returns:
        tuple: (response_dict, 403)
    """
    return error_response(message, status=403)


def not_found_response(message: str = 'Resource not found') -> tuple:
    """
    Convenience function for 404 Not Found responses.
    
    Args:
        message: Error message
        
    Returns:
        tuple: (response_dict, 404)
    """
    return error_response(message, status=404)
