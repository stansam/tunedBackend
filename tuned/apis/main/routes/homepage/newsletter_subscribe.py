"""
Newsletter subscription endpoint.

POST /api/newsletter/subscribe - Subscribe to newsletter
"""
from flask import request
from sqlalchemy.exc import IntegrityError
from tuned.main import main_bp
from tuned.main.schemas import NewsletterSubscribeSchema
from tuned.models.communication import NewsletterSubscriber
from tuned.models.audit import ActivityLog
from tuned.extensions import db
from tuned.utils.responses import (
    success_response,
    error_response,
    validation_error_response,
    created_response
)
from tuned.utils.decorators import rate_limit
from marshmallow import ValidationError
import logging

logger = logging.getLogger(__name__)


@main_bp.route('/api/newsletter/subscribe', methods=['POST'])
@rate_limit(max_requests=3, window=3600)  # 3 requests per hour
def subscribe_to_newsletter():
    """
    Subscribe to newsletter.
    
    Rate limited to 3 requests per hour per IP.
    
    Request body:
        - email: Email address (required)
        - name: Subscriber name (optional)
    
    Returns:
        JSON response with subscription status
    """
    try:
        # Validate request data
        schema = NewsletterSubscribeSchema()
        data = schema.load(request.get_json() or {})
        
    except ValidationError as err:
        return validation_error_response(err.messages)
    
    try:
        email = data['email']
        name = data.get('name', '')
        
        # Check if already subscribed
        existing = NewsletterSubscriber.query.filter_by(email=email).first()
        
        if existing:
            if existing.is_active:
                # Already subscribed and active
                logger.info(f'Newsletter subscription attempt for existing active email: {email}')
                return success_response(
                    {'subscribed': True, 'message': 'You are already subscribed to our newsletter'},
                    message='Already subscribed'
                )
            else:
                # Reactivate subscription
                existing.is_active = True
                existing.name = name if name else existing.name
                db.session.commit()
                
                logger.info(f'Newsletter subscription reactivated: {email}')
                
                # Send confirmation email
                try:
                    from tuned.services.newsletter_service import send_newsletter_subscription_email
                    send_newsletter_subscription_email(email, name)
                except Exception as email_err:
                    logger.error(f'Failed to send newsletter email: {str(email_err)}')
                
                # Log activity
                ActivityLog.log(
                    action='newsletter_resubscribed',
                    entity_type='NewsletterSubscriber',
                    entity_id=existing.id,
                    description=f'Newsletter subscription reactivated: {email}',
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
                )
                
                return success_response(
                    {'subscribed': True},
                    message='Successfully resubscribed to newsletter'
                )
        
        # Create new subscription
        subscriber = NewsletterSubscriber(
            email=email,
            name=name,
            is_active=True
        )
        
        db.session.add(subscriber)
        db.session.commit()
        
        logger.info(f'New newsletter subscription: {email}')
        
        # Send confirmation email
        try:
            from tuned.services.newsletter_service import send_newsletter_subscription_email
            send_newsletter_subscription_email(email, name)
        except Exception as email_err:
            logger.error(f'Failed to send newsletter email: {str(email_err)}')
            # Don't fail the subscription if email fails
        
        # Log activity
        ActivityLog.log(
            action='newsletter_subscribed',
            entity_type='NewsletterSubscriber',
            entity_id=subscriber.id,
            description=f'New newsletter subscription: {email}',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return created_response(
            {'subscribed': True},
            message='Successfully subscribed to newsletter'
        )
        
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f'Database integrity error in newsletter subscription: {str(e)}')
        return error_response(
            'Email already exists in our system',
            status=409
        )
    
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error processing newsletter subscription: {str(e)}')
        return error_response(
            'Failed to process subscription',
            status=500
        )
