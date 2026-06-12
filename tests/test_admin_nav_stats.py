import json
import pytest
from tuned.models import Order
from tuned.models.order import OrderComment
from tuned.models.content import Testimonial
from tuned.models.enums import OrderStatus

def test_admin_nav_stats_unauthenticated(client):
    response = client.get('/admin/nav-stats')
    # Unauthorized redirect or 401 response
    assert response.status_code in (302, 401)

def test_admin_nav_stats_unauthorized(client, sample_user, mock_redis):
    # Log in as non-admin user
    with client:
        client.post('/api/auth/login', 
                    data=json.dumps({'identifier': sample_user.email, 'password': 'TestPass123!'}),
                    content_type='application/json')
        
        response = client.get('/admin/nav-stats')
        # Expected: 403 Forbidden because is_admin is False
        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False
        assert data['message'] == "Administrator privilege required"

def test_admin_nav_stats_success(client, db, admin_user, mock_redis):
    # Create some dummy data in DB
    order1 = Order(
        client_id=admin_user.id,
        status=OrderStatus.PENDING,
        total_price=100.0,
        currency="USD",
        title="Test Order 1"
    )
    order2 = Order(
        client_id=admin_user.id,
        status=OrderStatus.COMPLETED_PENDING_REVIEW,
        total_price=150.0,
        currency="USD",
        paid=False,
        title="Test Order 2"
    )
    # Ensure ID is generated
    db.session.add_all([order1, order2])
    db.session.commit()

    comment = OrderComment(
        order_id=order1.id,
        user_id=admin_user.id,
        message="Hello!",
        is_admin=False,
        is_read=False
    )
    testimonial = Testimonial(
        user_id=admin_user.id,
        content="Great service!",
        rating=5,
        is_approved=False
    )
    db.session.add_all([comment, testimonial])
    db.session.commit()

    # Log in as admin user
    with client:
        client.post('/api/auth/login', 
                    data=json.dumps({'identifier': admin_user.email, 'password': 'AdminPass123!'}),
                    content_type='application/json')
        
        response = client.get('/admin/nav-stats')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['active_orders_count'] >= 1
        assert data['data']['payments_count'] >= 1
        assert data['data']['chat_count'] >= 1
        assert data['data']['testimonials_count'] >= 1
