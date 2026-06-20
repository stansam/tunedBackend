import json
import pytest
from datetime import datetime, timezone, timedelta
from tuned.models import User, Order
from tuned.models.preferences import UserLocalizationSettings
from tuned.models.enums import OrderStatus, PaymentStatus
from tuned.models.payment import Payment, AcceptedPaymentMethod
from tuned.core.events import get_event_bus

def test_admin_users_unauthenticated(client):
    for endpoint in ["stats", "geography", "export"]:
        response = client.get(f"/admin/users/{endpoint}")
        assert response.status_code in (302, 401)
    
    response = client.post("/admin/users/list", data=json.dumps({}), content_type="application/json")
    assert response.status_code in (302, 401)


def test_admin_users_unauthorized(client, sample_user, mock_redis):
    with client:
        client.post('/api/auth/login', 
                    data=json.dumps({'identifier': sample_user.email, 'password': 'TestPass123!'}),
                    content_type='application/json')
        
        for endpoint in ["stats", "geography", "export"]:
            response = client.get(f"/admin/users/{endpoint}")
            assert response.status_code == 403

        response = client.post("/admin/users/list", data=json.dumps({}), content_type="application/json")
        assert response.status_code == 403


def test_admin_users_success(client, db, admin_user, sample_user, mock_redis):
    # Set up some order and payment history for the sample user
    order = Order(
        client_id=sample_user.id,
        status=OrderStatus.COMPLETED,
        total_price=600.0,
        currency="USD",
        title="Admin Users Test Order",
        due_date=datetime.now(timezone.utc) - timedelta(days=2)
    )
    db.session.add(order)
    db.session.commit()

    method = AcceptedPaymentMethod(name="PayPal", category="digital_wallet")
    db.session.add(method)
    db.session.commit()

    payment = Payment(
        order_id=order.id,
        user_id=sample_user.id,
        amount=600.0,
        accepted_method_id=method.id,
        status=PaymentStatus.COMPLETED
    )
    db.session.add(payment)
    db.session.commit()

    # Create localization settings for geography test
    loc = UserLocalizationSettings(
        user_id=sample_user.id,
        country_code="US"
    )
    db.session.add(loc)
    db.session.commit()

    with client:
        client.post('/api/auth/login', 
                    data=json.dumps({'identifier': admin_user.email, 'password': 'AdminPass123!'}),
                    content_type='application/json')

        # Test users stats
        resp_stats = client.get("/admin/users/stats")
        assert resp_stats.status_code == 200
        data_stats = resp_stats.get_json()
        assert data_stats["success"] is True
        assert data_stats["data"]["total_clients"] >= 1
        assert data_stats["data"]["high_value_clients_count"] >= 1

        # Test users list (POST)
        resp_list = client.post("/admin/users/list", 
                                data=json.dumps({"page": 1, "per_page": 5}), 
                                content_type="application/json")
        assert resp_list.status_code == 200
        data_list = resp_list.get_json()
        assert data_list["success"] is True
        assert data_list["data"]["total"] >= 1
        assert len(data_list["data"]["users"]) >= 1
        assert data_list["data"]["users"][0]["email"] == sample_user.email
        assert data_list["data"]["users"][0]["clv_status"] == "high"

        # Test users geography
        resp_geo = client.get("/admin/users/geography")
        assert resp_geo.status_code == 200
        data_geo = resp_geo.get_json()
        assert data_geo["success"] is True
        assert len(data_geo["data"]) >= 1
        assert data_geo["data"][0]["country_code"] == "US"

        # Test users broadcast (POST)
        resp_broadcast = client.post("/admin/users/broadcast", 
                                     data=json.dumps({"message": "Hello all!"}), 
                                     content_type="application/json")
        assert resp_broadcast.status_code == 200
        data_broad = resp_broadcast.get_json()
        assert data_broad["success"] is True

        # Test message user (POST)
        resp_msg = client.post(f"/admin/users/{sample_user.id}/message", 
                               data=json.dumps({"message": "Hello you!"}), 
                               content_type="application/json")
        assert resp_msg.status_code == 200
        data_msg = resp_msg.get_json()
        assert data_msg["success"] is True

        # Test users export (GET)
        resp_export = client.get("/admin/users/export")
        assert resp_export.status_code == 200
        assert resp_export.headers["Content-Type"] == "text/csv"
        assert "users.csv" in resp_export.headers["Content-Disposition"]
        csv_data = resp_export.data.decode("utf-8")
        assert sample_user.email in csv_data


def test_user_registration_initializes_preferences(db, sample_user, mocker):
    # Mock get_country_code_from_ip to return "KE" for a valid IP address
    mocker.patch("tuned.interface.users.events.get_country_code_from_ip", return_value="KE")

    # Manually delete existing localization preferences for this user to test initialization
    loc_pref = db.session.query(UserLocalizationSettings).filter_by(user_id=sample_user.id).first()
    if loc_pref:
        db.session.delete(loc_pref)
        db.session.commit()

    # Trigger user.registered event
    get_event_bus().emit("user.registered", {
        "user_id": str(sample_user.id),
        "raw_token": "some-token",
        "email": sample_user.email,
        "name": sample_user.get_name(),
        "ip_address": "8.8.8.8"
    })

    # Assert settings were created and country_code set to KE
    db.session.expire_all()
    loc_settings = db.session.query(UserLocalizationSettings).filter_by(user_id=sample_user.id).first()
    assert loc_settings is not None
    assert loc_settings.country_code == "KE"
