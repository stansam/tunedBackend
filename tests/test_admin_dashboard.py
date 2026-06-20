import json
import pytest
from datetime import datetime, timezone
from tuned.models import Order, User
from tuned.models.payment import Payment, AcceptedPaymentMethod
from tuned.models.deadline_extension import OrderDeadlineExtensionRequest
from tuned.models.enums import OrderStatus, PaymentStatus, ExtensionRequestStatus, Priority
from tuned.models.audit import ActivityLog

def test_admin_dashboard_unauthenticated(client):
    for endpoint in ["kpis", "analytics", "tracking", "alerts"]:
        response = client.get(f"/admin/dashboard/{endpoint}")
        assert response.status_code in (302, 401)

def test_admin_dashboard_unauthorized(client, sample_user, mock_redis):
    with client:
        client.post('/api/auth/login', 
                    data=json.dumps({'identifier': sample_user.email, 'password': 'TestPass123!'}),
                    content_type='application/json')
        for endpoint in ["kpis", "analytics", "tracking", "alerts"]:
            response = client.get(f"/admin/dashboard/{endpoint}")
            assert response.status_code == 403

def test_admin_dashboard_success(client, db, admin_user, mock_redis):
    # Setup test data
    order = Order(
        client_id=admin_user.id,
        status=OrderStatus.PENDING,
        total_price=100.0,
        currency="USD",
        title="Admin Test Order 1",
        due_date=datetime.now(timezone.utc)
    )
    order_review = Order(
        client_id=admin_user.id,
        status=OrderStatus.COMPLETED_PENDING_REVIEW,
        total_price=200.0,
        currency="USD",
        title="Admin Test Order 2",
        due_date=datetime.now(timezone.utc)
    )
    db.session.add_all([order, order_review])
    db.session.commit()

    # Setup payment method and payment
    method = AcceptedPaymentMethod(name="PayPal", category="digital_wallet")
    db.session.add(method)
    db.session.commit()

    payment = Payment(
        order_id=order.id,
        user_id=admin_user.id,
        amount=100.0,
        accepted_method_id=method.id,
        status=PaymentStatus.COMPLETED
    )
    db.session.add(payment)
    db.session.commit()

    # Setup extension request
    extension = OrderDeadlineExtensionRequest(
        order_id=order.id,
        requested_by=admin_user.id,
        requested_hours=24,
        reason="Need more time",
        original_due_date=datetime.now(timezone.utc),
        status=ExtensionRequestStatus.PENDING,
        priority=Priority.NORMAL
    )
    db.session.add(extension)
    db.session.commit()

    # Setup Activity Log
    act_log = ActivityLog(
        user_id=admin_user.id,
        action="order_created",
        entity_type="Order",
        entity_id=order.id
    )
    db.session.add(act_log)
    db.session.commit()

    with client:
        client.post('/api/auth/login', 
                    data=json.dumps({'identifier': admin_user.email, 'password': 'AdminPass123!'}),
                    content_type='application/json')
        
        # Test KPIs
        resp_kpis = client.get("/admin/dashboard/kpis")
        assert resp_kpis.status_code == 200
        data_kpis = resp_kpis.get_json()
        assert data_kpis["success"] is True
        assert data_kpis["data"]["active_orders"] >= 1
        assert data_kpis["data"]["total_revenue"] >= 100.0
        assert data_kpis["data"]["pending_actions"] >= 2  # 1 pending review + 1 extension request

        # Test Analytics
        resp_analytics = client.get("/admin/dashboard/analytics")
        assert resp_analytics.status_code == 200
        data_analytics = resp_analytics.get_json()
        assert data_analytics["success"] is True
        assert "spending_velocity" in data_analytics["data"]
        assert "project_lifecycle" in data_analytics["data"]

        # Test Tracking
        resp_tracking = client.get("/admin/dashboard/tracking")
        assert resp_tracking.status_code == 200
        data_tracking = resp_tracking.get_json()
        assert data_tracking["success"] is True
        assert len(data_tracking["data"]["upcoming_deadlines"]) >= 1
        assert len(data_tracking["data"]["activity_feed"]) >= 1

        # Test Alerts
        resp_alerts = client.get("/admin/dashboard/alerts")
        assert resp_alerts.status_code == 200
        data_alerts = resp_alerts.get_json()
        assert data_alerts["success"] is True
        assert len(data_alerts["data"]["alerts"]) >= 2
