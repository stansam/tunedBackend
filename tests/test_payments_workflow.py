import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
import uuid
from flask import Flask

from tuned.models import (
    PaymentStatus, MethodCategory, OrderStatus, AcceptedPaymentMethod, 
    Payment, Order, User, NotificationType
)
from tuned.interface.payment.pesapal import PesapalHelper
from tuned.interface.payment.payment import ClientMarkAsPaid, AdminVerifyPayment

# Construct a real Flask instance for context bindings
test_app = Flask("tuned_test")
test_app.config.update({
    "PESAPAL_CONSUMER_KEY": "dummy_key",
    "PESAPAL_CONSUMER_SECRET": "dummy_secret",
    "PESAPAL_SANDBOX": True,
    "PESAPAL_IPN_URL": "http://localhost:5000/ipn",
    "PESAPAL_CALLBACK_URL": "http://localhost:3000/callback"
})

class TestPaymentsWorkflow(unittest.TestCase):
    def setUp(self):
        # Push the flask app context so proxy lookups succeed
        self.ctx = test_app.app_context()
        self.ctx.push()

        self.mock_session = MagicMock()
        self.mock_repos = MagicMock()
        self.mock_repos.session = self.mock_session
        
        self.client_id = uuid.uuid4()
        self.order_id = uuid.uuid4()
        self.payment_id = uuid.uuid4()
        self.method_id = uuid.uuid4()

    def tearDown(self):
        self.ctx.pop()

    @patch('tuned.interface.payment.pesapal.requests.post')
    def test_pesapal_helper_auth_token_caching(self, mock_post):
        # Setup mock authentication response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "token": "cached_access_token_123",
            "expiryDate": "2026-05-20T23:59:59Z"
        }
        mock_post.return_value = mock_response

        # Clear token cache before test
        PesapalHelper._token = None
        PesapalHelper._token_expires = None

        # Instantiate helper
        helper = PesapalHelper()
        token1 = helper.get_token()
        
        # Call again, should return cached token without requesting API again
        token2 = helper.get_token()

        self.assertEqual(token1, "cached_access_token_123")
        self.assertEqual(token2, "cached_access_token_123")
        
        # Verify post was called exactly once due to caching
        mock_post.assert_called_once()

    @patch('tuned.interface.payment.pesapal.requests.get')
    @patch('tuned.interface.payment.pesapal.requests.post')
    def test_pesapal_helper_submit_order(self, mock_post, mock_get):
        # Mock auth token
        helper = PesapalHelper()
        PesapalHelper._token = "valid_token"
        PesapalHelper._token_expires = datetime.now(timezone.utc).timestamp() + 3600

        # Mock IPN listing response to avoid API calls out to Pesapal
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = [
            {"url": "http://localhost:5000/ipn", "ipn_id": "ipn-12345"}
        ]
        mock_get.return_value = mock_get_response

        # Mock submit order response
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            "redirect_url": "https://cyb.pesapal.com/payment/redirect",
            "order_tracking_id": "tracking-12345",
            "status": "200"
        }
        mock_post.return_value = mock_post_response

        res = helper.submit_order(
            order_id=str(self.order_id),
            amount=150.0,
            email="client@example.com",
            phone="0700000000",
            first_name="John",
            last_name="Doe",
            description="Fulfillment Payment"
        )

        self.assertEqual(res["redirect_url"], "https://cyb.pesapal.com/payment/redirect")
        self.assertEqual(res["order_tracking_id"], "tracking-12345")

    def test_client_mark_as_paid(self):
        # Create a payment record mock
        payment = MagicMock(spec=Payment)
        payment.id = self.payment_id
        payment.status = PaymentStatus.PENDING

        self.mock_repos.payment.payment.get_by_id.return_value = payment
        
        # When update is called, mutate status to pending_verification
        def update_mock(pid, update_dto):
            payment.status = update_dto.status
            payment.client_proof_reference = update_dto.client_proof_reference
            return payment
        self.mock_repos.payment.payment.update.side_effect = update_mock

        marker = ClientMarkAsPaid(self.mock_repos)
        updated = marker.execute(str(self.payment_id), "ref-999", str(self.client_id))

        # Verify status transitions to pending_verification and reference is stored
        self.assertEqual(updated.status, PaymentStatus.PENDING_VERIFICATION)
        self.assertEqual(updated.client_proof_reference, "ref-999")

    @patch('tuned.interface.payment.payment.event_bus')
    def test_admin_verify_payment(self, mock_event_bus):
        # Mock payment, order and repository layers
        payment = MagicMock(spec=Payment)
        payment.id = self.payment_id
        payment.status = PaymentStatus.PENDING_VERIFICATION
        payment.order_id = self.order_id
        payment.user_id = self.client_id
        payment.amount = 120.0
        payment.accepted_method = MagicMock()
        payment.accepted_method.name = "Bank Deposit"

        order = MagicMock(spec=Order)
        order.id = self.order_id
        order.client_id = self.client_id
        order.total_price = 120.0
        order.subtotal = 120.0
        order.discount_amount = 0.0
        order.paid = False
        order.status = OrderStatus.PENDING

        self.mock_repos.payment.payment.get_by_id.return_value = payment
        self.mock_repos.order.get_by_id.return_value = order
        
        # When update is called, mutate status to completed
        def update_mock(pid, update_dto):
            payment.status = update_dto.status
            return payment
        self.mock_repos.payment.payment.update.side_effect = update_mock
        
        # Configure scalar mock to return the mock order
        self.mock_session.scalar.return_value = order

        # Initialize and run verifier
        verifier = AdminVerifyPayment(self.mock_repos)
        updated = verifier.execute(str(self.payment_id), "admin-id")

        # Check order is marked as paid and active
        self.assertTrue(order.paid)
        self.assertEqual(order.status, OrderStatus.ACTIVE)

        # Check invoice is created
        self.mock_repos.payment.invoice.create.assert_called_once()
        
        # Check event bus emitted success
        mock_event_bus.emit.assert_any_call("payment.verified_by_admin", {
            "payment_id": payment.id,
            "order_id": payment.order_id,
            "user_id": payment.user_id,
            "status": PaymentStatus.COMPLETED
        })

if __name__ == '__main__':
    unittest.main()
