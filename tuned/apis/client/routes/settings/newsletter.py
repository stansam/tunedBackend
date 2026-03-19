"""
Newsletter subscription routes for client blueprint.

Handles newsletter subscriptions, preferences, and unsubscribe requests.
"""

from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from datetime import datetime, timezone
import logging

from tuned.client import client_bp
from tuned.client.schemas import (
    NewsletterSubscribeSchema,
    NewsletterUnsubscribeSchema,
    NewsletterPreferencesSchema
)
from tuned.models.user import User
from tuned.extensions import db
from tuned.utils import success_response, error_response, validation_error_response, created_response
from tuned.utils.decorators import rate_limit, log_activity
from tuned.services.email_service import send_newsletter_welcome_email, send_newsletter_goodbye_email

logger = logging.getLogger(__name__)


@client_bp.route('/newsletter/subscribe', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=10, window=3600)
@log_activity('newsletter_subscribed', 'User')
def subscribe_newsletter():
    """
    Subscribe to newsletter.
    
    Request Body:
        {
            "email": str (optional, uses user's email if not provided),
            "name": str (optional),
            "preferences": dict (optional),
            "topics": list (optional)
        }
    
    Returns:
        201: Successfully subscribed
        400: Validation error or already subscribed
    """
    current_user_id = get_jwt_identity()
    
    # Validate input
    schema = NewsletterSubscribeSchema()
    try:
        data = schema.load(request.get_json() or {})
    except ValidationError as e:
        return validation_error_response(e.messages)
    
    try:
        user = User.query.get(current_user_id)
        
        if not user:
            return error_response('User not found', status=404)
        
        email = data.get('email', user.email)
        name = data.get('name', user.get_name())
        topics = data.get('topics', [])
        
        # In a full implementation, create NewsletterSubscriber model entry
        # For now, just log the subscription
        
        logger.info(f'Newsletter subscription: {email} (user {current_user_id}), topics: {topics}')
        
        # Send welcome email
        try:
            send_newsletter_welcome_email(email, name)
        except Exception as e:
            logger.error(f'Error sending newsletter welcome email: {str(e)}')
        
        subscription_data = {
            'email': email,
            'name': name,
            'topics': topics,
            'subscribed_at': datetime.now(timezone.utc).isoformat(),
            'status': 'active'
        }
        
        return created_response(
            data={'subscription': subscription_data},
            message='Successfully subscribed to newsletter'
        )
        
    except Exception as e:
        logger.error(f'Error subscribing to newsletter for user {current_user_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while subscribing to the newsletter', status=500)


@client_bp.route('/newsletter/unsubscribe', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=10, window=3600)
@log_activity('newsletter_unsubscribed', 'User')
def unsubscribe_newsletter():
    """
    Unsubscribe from newsletter.
    
    Request Body:
        {
            "reason": str (optional: too_many_emails, not_relevant, never_signed_up, privacy_concerns, other),
            "feedback": str (optional, max 500 chars),
            "unsubscribe_all": bool (optional, default true)
        }
    
    Returns:
        200: Successfully unsubscribed
    """
    current_user_id = get_jwt_identity()
    
    # Validate input
    schema = NewsletterUnsubscribeSchema()
    try:
        data = schema.load(request.get_json() or {})
    except ValidationError as e:
        return validation_error_response(e.messages)
    
    try:
        user = User.query.get(current_user_id)
        
        if not user:
            return error_response('User not found', status=404)
        
        reason = data.get('reason', 'other')
        feedback = data.get('feedback')
        unsubscribe_all = data.get('unsubscribe_all', True)
        
        # In a full implementation, update NewsletterSubscriber model
        # For now, just log the unsubscribe
        
        logger.info(
            f'Newsletter unsubscribe: {user.email} (user {current_user_id}), '
            f'reason: {reason}, all: {unsubscribe_all}'
        )
        
        # Send goodbye email
        try:
            send_newsletter_goodbye_email(user.email, user.get_name())
        except Exception as e:
            logger.error(f'Error sending newsletter goodbye email: {str(e)}')
        
        return success_response(
            message='Successfully unsubscribed from newsletter. We\'re sorry to see you go!'
        )
        
    except Exception as e:
        logger.error(f'Error unsubscribing from newsletter for user {current_user_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while unsubscribing', status=500)


@client_bp.route('/newsletter/preferences', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=100, window=60)
def get_newsletter_preferences():
    """
    Get newsletter subscription preferences.
    
    Returns:
        200: Newsletter preferences
    """
    current_user_id = get_jwt_identity()
    
    try:
        user = User.query.get(current_user_id)
        
        if not user:
            return error_response('User not found', status=404)
        
        # In a full implementation, query NewsletterSubscriber model
        preferences = {
            'subscribed': False,  # Default
            'email': user.email,
            'frequency': 'weekly',
            'topics': [],
            'format': 'html'
        }
        
        return success_response(
            data={'preferences': preferences},
            message='Newsletter preferences retrieved successfully'
        )
        
    except Exception as e:
        logger.error(f'Error retrieving newsletter preferences for user {current_user_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while retrieving newsletter preferences', status=500)


@client_bp.route('/newsletter/preferences', methods=['PUT'])
@jwt_required()
@rate_limit(max_requests=20, window=3600)
@log_activity('newsletter_preferences_updated', 'User')
def update_newsletter_preferences():
    """
    Update newsletter subscription preferences.
    
    Request Body:
        {
            "frequency": str (optional: daily, weekly, biweekly, monthly),
            "topics": list (optional: academic_tips, writing_guides, discounts, company_news, success_stories, industry_news),
            "format": str (optional: html, text)
        }
    
    Returns:
        200: Preferences updated successfully
        400: Validation error
    """
    current_user_id = get_jwt_identity()
    
    # Validate input
    schema = NewsletterPreferencesSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as e:
        return validation_error_response(e.messages)
    
    try:
        user = User.query.get(current_user_id)
        
        if not user:
            return error_response('User not found', status=404)
        
        # In a full implementation, update NewsletterSubscriber model
        # For now, just log the update
        
        logger.info(
            f'Newsletter preferences updated for user {current_user_id}: '
            f'frequency={data.get("frequency")}, topics={data.get("topics")}'
        )
        
        return success_response(
            data={'preferences': data},
            message='Newsletter preferences updated successfully'
        )
        
    except Exception as e:
        logger.error(f'Error updating newsletter preferences for user {current_user_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while updating newsletter preferences', status=500)
