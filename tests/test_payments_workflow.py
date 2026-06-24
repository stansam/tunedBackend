import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta
import uuid
from flask import Flask

from tuned.models import (
    PaymentStatus, MethodCategory, OrderStatus, AcceptedPaymentMethod, 
    Payment, Order, User, TransactionType, TransactionStatus, Currency
)
from tuned.dtos.payment import (
    PaymentCreateDTO, PaymentUpdateDTO, TransactionCreateDTO,
    PesapalSubmitOrderDTO, PesapalSubmitOrderResponseDTO,
    PesapalTransactionStatusDTO
)
from tuned.interface.payment.pesapal import PesapalHelper
from tuned.interface.payment.payment import (
    ClientMarkAsPaid, AdminVerifyPayment,
    InitiatePesapalCheckout, HandlePesapalIpn, AdminRejectPayment
)
from tuned.repository.payment.payment import(
    CreatePayment, UpdatePayment,
    GetPaymentByPesapalTrackingId, GetActivePaymentForOrder
)

# Construct a real Flask instance for context bindings
test_app = Flask("tuned_test")
test_app.config.update({
    "PESAPAL_CONSUMER_KEY": "dummy_key",
    "PESAPAL_CONSUMER_SECRET": "dummy_secret",
    "PESAPAL_SANDBOX": True,
    "PESAPAL_IPN_URL": "http://localhost:5000/ipn",
    "PESAPAL_CALLBACK_URL": "http://localhost:3000/callback",
    "LOGIN_DISABLED": True
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

        # Mock Redis client
        self.mock_redis = MagicMock()
        self.redis_patcher = patch('tuned.interface.payment.pesapal.get_redis_client', return_value=self.mock_redis)
        self.redis_patcher.start()

    def tearDown(self):
        self.redis_patcher.stop()
        self.ctx.pop()

    @patch('tuned.interface.payment.pesapal.requests.Session')
    def test_pesapal_helper_auth_token_caching(self, mock_session_cls):
        # Setup mock session instance
        mock_session_instance = MagicMock()
        mock_session_cls.return_value = mock_session_instance

        # Setup mock authentication response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "token": "cached_access_token_123",
            "expiryDate": "2026-05-20T23:59:59Z"
        }
        mock_session_instance.post.return_value = mock_response

        # Mock redis to return None first (uncached) then cached token
        self.mock_redis.get.side_effect = [None, "cached_access_token_123"]

        helper = PesapalHelper()
        token1 = helper.get_token()
        
        # Second call should fetch from Redis cache (simulated by side_effect returning cached token)
        token2 = helper.get_token()

        self.assertEqual(token1, "cached_access_token_123")
        self.assertEqual(token2, "cached_access_token_123")
        
        # Verify post was called exactly once
        mock_session_instance.post.assert_called_once()
        self.mock_redis.setex.assert_called_once()

    @patch('tuned.interface.payment.pesapal.requests.Session')
    def test_pesapal_helper_submit_order(self, mock_session_cls):
        # Setup mock session instance
        mock_session_instance = MagicMock()
        mock_session_cls.return_value = mock_session_instance

        # Mock auth token in Redis
        self.mock_redis.get.return_value = "valid_token"

        # Mock IPN listing response to avoid API calls out to Pesapal
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = [
            {"url": "http://localhost:5000/ipn", "ipn_id": "ipn-12345"}
        ]
        mock_session_instance.get.return_value = mock_get_response

        # Mock submit order response
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            "redirect_url": "https://cyb.pesapal.com/payment/redirect",
            "order_tracking_id": "tracking-12345",
            "status": "200"
        }
        mock_session_instance.post.return_value = mock_post_response

        helper = PesapalHelper()
        dto = PesapalSubmitOrderDTO(
            merchant_reference="PAY-123456",
            amount=150.0,
            currency="USD",
            email="client@example.com",
            phone="0700000000",
            first_name="John",
            last_name="Doe",
            description="Fulfillment Payment"
        )
        res = helper.submit_order(dto)

        self.assertEqual(res.redirect_url, "https://cyb.pesapal.com/payment/redirect")
        self.assertEqual(res.order_tracking_id, "tracking-12345")
        self.assertEqual(res.merchant_reference, "PAY-123456")

    def test_client_mark_as_paid(self):
        # Create a payment record mock
        payment = MagicMock(spec=Payment)
        payment.id = self.payment_id
        payment.status = PaymentStatus.PENDING
        payment.accepted_method_id = self.method_id

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
        payment.payment_id = "PAY-12345"
        payment.status = PaymentStatus.PENDING_VERIFICATION
        payment.order_id = self.order_id
        payment.user_id = self.client_id
        payment.amount = 120.0
        payment.accepted_method_id = self.method_id

        order = MagicMock(spec=Order)
        order.id = self.order_id
        order.client_id = self.client_id
        order.order_number = "ORD-777"
        order.total_price = 120.0
        order.subtotal = 120.0
        order.discount_amount = 0.0
        order.paid = False
        order.status = OrderStatus.PENDING

        self.mock_repos.payment.payment.get_by_id.return_value = payment
        self.mock_repos.order.get_by_id.return_value = order

        # Setup mock user and mock invoice
        mock_user = MagicMock()
        mock_user.get_name.return_value = "Test User"
        mock_user.email = "test@example.com"
        self.mock_repos.user.get_user_by_id.return_value = mock_user

        mock_invoice = MagicMock()
        mock_invoice.id = uuid.uuid4()
        mock_invoice.invoice_number = "INV-777"
        self.mock_repos.payment.invoice.create.return_value = mock_invoice
        
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
            "payment_id": str(payment.id),
            "payment_ref": "PAY-12345",
            "order_id": str(payment.order_id),
            "order_number": "ORD-777",
            "user_id": str(payment.user_id),
            "client_name": "Test User",
            "client_email": "test@example.com",
            "status": "completed",
            "amount": 120.0,
            "is_automated": False,
            "invoice_id": str(mock_invoice.id),
            "invoice_number": "INV-777",
        })

    def test_create_payment_enum_handling(self):
        # Test that CreatePayment repository handles both strings and enum objects
        creator = CreatePayment(self.mock_session)
        
        # 1. Test with string
        data_str = PaymentCreateDTO(
            order_id=str(self.order_id),
            user_id=str(self.client_id),
            amount=50.0,
            accepted_method_id=str(self.method_id),
            status="pending"
        )
        # We can flush mock_session to bypass DB checks
        with patch('tuned.repository.payment.payment.Payment') as mock_payment_cls:
            creator.execute(data_str)
            mock_payment_cls.assert_called_with(
                order_id=self.order_id,
                user_id=self.client_id,
                amount=50.0,
                accepted_method_id=self.method_id,
                status=PaymentStatus.PENDING
            )

        # 2. Test with enum
        data_enum = PaymentCreateDTO(
            order_id=str(self.order_id),
            user_id=str(self.client_id),
            amount=50.0,
            accepted_method_id=str(self.method_id),
            status=PaymentStatus.COMPLETED
        )
        with patch('tuned.repository.payment.payment.Payment') as mock_payment_cls:
            creator.execute(data_enum)
            mock_payment_cls.assert_called_with(
                order_id=self.order_id,
                user_id=self.client_id,
                amount=50.0,
                accepted_method_id=self.method_id,
                status=PaymentStatus.COMPLETED
            )

    @patch('tuned.interface.payment.payment.event_bus')
    @patch('tuned.interface.payment.pesapal.PesapalHelper')
    def test_initiate_pesapal_checkout(self, mock_pesapal_helper_cls, mock_event_bus):
        # Configure submit order mock response
        mock_helper = MagicMock()
        mock_helper.submit_order.return_value = PesapalSubmitOrderResponseDTO(
            redirect_url="http://pay.pesapal.com/redirect",
            order_tracking_id="track-999",
            merchant_reference="PAY-REF123"
        )
        mock_pesapal_helper_cls.return_value = mock_helper

        # Setup mocks on repository
        created_payment = MagicMock()
        created_payment.id = self.payment_id
        created_payment.payment_id = "PAY-REF123"
        created_payment.amount = 100.0
        
        updated_payment = MagicMock()
        updated_payment.id = self.payment_id
        updated_payment.payment_id = "PAY-REF123"
        updated_payment.amount = 100.0
        updated_payment.pesapal_tracking_id = "track-999"

        self.mock_repos.payment.payment.create.return_value = created_payment
        self.mock_repos.payment.payment.update.return_value = updated_payment

        checkout = InitiatePesapalCheckout(self.mock_repos)
        result = checkout.execute(
            order_id=str(self.order_id),
            user_id=str(self.client_id),
            amount=100.0,
            method_id=str(self.method_id),
            user_data={"email": "client@example.com", "order_number": "ORD-123"}
        )

        self.assertEqual(result["redirect_url"], "http://pay.pesapal.com/redirect")
        self.assertEqual(result["order_tracking_id"], "track-999")
        self.assertEqual(result["payment_id"], str(self.payment_id))

        # Check payment record is created first, then updated with the tracking id
        self.mock_repos.payment.payment.create.assert_called_once()
        self.mock_repos.payment.payment.update.assert_called_with(
            str(self.payment_id),
            PaymentUpdateDTO(pesapal_tracking_id="track-999")
        )

        # Check transaction record was logged as pending
        self.mock_repos.payment.transaction.create.assert_called_once()
        tx_dto = self.mock_repos.payment.transaction.create.call_args[0][0]
        self.assertEqual(tx_dto.status, TransactionStatus.PENDING)
        self.assertEqual(tx_dto.reference, "track-999")

        # Check event emit
        mock_event_bus.emit.assert_called_with("payment.pesapal_initiated", {
            "payment_id": str(self.payment_id),
            "payment_ref": "PAY-REF123",
            "order_id": str(self.order_id),
            "user_id": str(self.client_id),
            "tracking_id": "track-999",
            "amount": 100.0
        })

    @patch('tuned.interface.payment.payment.AdminVerifyPayment')
    def test_handle_pesapal_ipn_completed(self, mock_verify_cls):
        # Mock payment record lookup
        payment = MagicMock(spec=Payment)
        payment.id = self.payment_id
        payment.payment_id = "PAY-REF123"
        payment.status = PaymentStatus.PENDING

        self.mock_repos.payment.payment.get_by_pesapal_tracking_id.return_value = payment

        # Mock AdminVerifyPayment execution
        mock_verify_instance = MagicMock()
        mock_verify_cls.return_value = mock_verify_instance

        handler = HandlePesapalIpn(self.mock_repos)
        status_dto = PesapalTransactionStatusDTO(
            payment_status_description="Completed",
            amount=100.0,
            currency="USD",
            payment_method="card",
            order_tracking_id="track-999",
            merchant_reference="PAY-REF123"
        )
        res = handler.execute("track-999", status_dto)

        # Assert correct view delegation
        self.assertEqual(res["status"], "completed")
        mock_verify_instance.execute.assert_called_with(
            payment_id=str(self.payment_id),
            admin_id="system_pesapal"
        )

    def test_handle_pesapal_ipn_idempotency(self):
        # If payment is already completed, it should return already_completed and skip verification
        payment = MagicMock(spec=Payment)
        payment.id = self.payment_id
        payment.payment_id = "PAY-REF123"
        payment.status = PaymentStatus.COMPLETED

        self.mock_repos.payment.payment.get_by_pesapal_tracking_id.return_value = payment

        handler = HandlePesapalIpn(self.mock_repos)
        status_dto = PesapalTransactionStatusDTO(
            payment_status_description="Completed",
            amount=100.0,
            currency="USD",
            payment_method="card",
            order_tracking_id="track-999",
            merchant_reference="PAY-REF123"
        )
        res = handler.execute("track-999", status_dto)

        self.assertEqual(res["status"], "already_completed")

    @patch('tuned.interface.payment.payment.AdminRejectPayment')
    def test_handle_pesapal_ipn_failed(self, mock_reject_cls):
        # Mock payment record lookup
        payment = MagicMock(spec=Payment)
        payment.id = self.payment_id
        payment.payment_id = "PAY-REF123"
        payment.status = PaymentStatus.PENDING

        self.mock_repos.payment.payment.get_by_pesapal_tracking_id.return_value = payment

        # Mock AdminRejectPayment execution
        mock_reject_instance = MagicMock()
        mock_reject_cls.return_value = mock_reject_instance

        handler = HandlePesapalIpn(self.mock_repos)
        status_dto = PesapalTransactionStatusDTO(
            payment_status_description="Failed",
            amount=100.0,
            currency="USD",
            payment_method="card",
            order_tracking_id="track-999",
            merchant_reference="PAY-REF123"
        )
        res = handler.execute("track-999", status_dto)

        # Assert correct view delegation
        self.assertEqual(res["status"], "failed")
        mock_reject_instance.execute.assert_called_with(
            payment_id=str(self.payment_id),
            user_id="system_pesapal",
            rejection_reason="Pesapal gateway reported payment as failed."
        )

    def test_exception_translation(self):
        from tuned.repository import exceptions as repo_exc
        from tuned.core import exceptions as core_exc
        from tuned.interface.payment.payment import _translate_exception

        # Test NotFound translation
        exc = repo_exc.NotFound("Record not found")
        translated = _translate_exception(exc)
        self.assertIsInstance(translated, core_exc.NotFound)

        # Test ValidationError translation
        exc = repo_exc.ValidationError("Invalid input")
        translated = _translate_exception(exc)
        self.assertIsInstance(translated, core_exc.ValidationError)

        # Test AlreadyExists translation
        exc = repo_exc.AlreadyExists("Duplicate key")
        translated = _translate_exception(exc)
        self.assertIsInstance(translated, core_exc.AlreadyExists)

    def test_service_rollback_on_failure(self):
        from tuned.repository import exceptions as repo_exc
        from tuned.core import exceptions as core_exc
        from tuned.interface.payment.payment import ProcessPayment

        # Setup mock repo to raise RepositoryException on create
        self.mock_repos.payment.payment.create.side_effect = repo_exc.RepositoryException("Database crash")

        data = PaymentCreateDTO(
            order_id=str(self.order_id),
            user_id=str(self.client_id),
            amount=50.0,
            accepted_method_id=str(self.method_id),
            status="pending"
        )

        processor = ProcessPayment(self.mock_repos)
        with self.assertRaises(core_exc.ServiceError):
            processor.execute(data)

        # Verify rollback was called on repository
        self.mock_repos.payment.rollback.assert_called_once()

    @patch('tuned.apis.payments.routes.payment.get_services')
    @patch('tuned.apis.payments.routes.payment.current_user')
    def test_resolve_payment_reference_route(self, mock_current_user, mock_get_services):
        from tuned.core.exceptions import NotFound

        # Setup current user
        mock_current_user.id = self.client_id
        mock_current_user.is_admin = False

        # Mock payment object
        mock_payment = MagicMock()
        mock_payment.id = self.payment_id
        mock_payment.payment_id = "PAY-RESOLVE"
        mock_payment.order_id = self.order_id
        mock_payment.user_id = self.client_id
        mock_payment.amount = 150.0
        mock_payment.status = PaymentStatus.PENDING

        mock_service = MagicMock()
        mock_get_services.return_value = mock_service

        # 1. Success case: Same user resolves reference
        mock_service.payment.payment.get_by_reference.return_value = mock_payment
        
        with test_app.test_request_context():
            from tuned.apis.payments.routes.payment import ResolvePaymentReferenceView
            view = ResolvePaymentReferenceView.as_view("resolve_payment")
            response, status_code = view(payment_ref="PAY-RESOLVE")
            
            self.assertEqual(status_code, 200)
            data = response.get_json()
            self.assertTrue(data["success"])
            self.assertEqual(data["data"]["payment_id"], "PAY-RESOLVE")

        # 2. Forbidden case: Different user attempts to resolve reference
        mock_current_user.id = uuid.uuid4() # change user ID
        
        with test_app.test_request_context():
            response, status_code = view(payment_ref="PAY-RESOLVE")
            self.assertEqual(status_code, 403)
            data = response.get_json()
            self.assertFalse(data["success"])
            self.assertIn("Access denied", data["message"])

        # 3. NotFound case: reference does not exist
        # Reset current user to owner
        mock_current_user.id = self.client_id
        mock_service.payment.payment.get_by_reference.side_effect = NotFound("Payment not found")

        with test_app.test_request_context():
            response, status_code = view(payment_ref="PAY-NOT-FOUND")
            self.assertEqual(status_code, 404)
            data = response.get_json()
            self.assertFalse(data["success"])
            self.assertIn("Payment not found", data["message"])

if __name__ == '__main__':
    unittest.main()
