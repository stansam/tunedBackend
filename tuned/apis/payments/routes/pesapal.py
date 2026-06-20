import logging
from flask import request, current_app, jsonify
from flask.views import MethodView
from tuned.utils.responses import error_response
from tuned.utils.dependencies import get_services
from tuned.utils.auth import get_user_ip
from tuned.utils.decorators import rate_limit

logger = logging.getLogger(__name__)

class PesapalIpnView(MethodView):
    decorators = [rate_limit(max_requests=30, window=60, key_prefix="pesapal_ipn")]

    def get(self):
        if current_app.config.get("FLASK_ENV") == "production":
            from tuned.interface.payment.pesapal import PESAPAL_IPN_ALLOWED_IPS
            caller_ip = get_user_ip()
            if caller_ip not in PESAPAL_IPN_ALLOWED_IPS:
                logger.warning("[IPN] Rejected request from unauthorized IP: %s", caller_ip)
                return error_response(message="Forbidden", status=403)

        services = None
        try:
            services = get_services()
            order_tracking_id = request.args.get("OrderTrackingId")
            order_merchant_ref = request.args.get("OrderMerchantReference")
            notif_type = request.args.get("OrderNotificationType")

            if not order_tracking_id:
                logger.error("[IPN] Missing OrderTrackingId parameter")
                return current_app.response_class(
                    response='{"response":"ERR","message":"Missing OrderTrackingId"}',
                    status=200,
                    mimetype='application/json',
                )

            logger.info("[IPN] Received: TrackingId=%s, MerchantRef=%s, Type=%s",
                        order_tracking_id, order_merchant_ref, notif_type)

            from tuned.interface.payment.pesapal import PesapalHelper
            pesapal = PesapalHelper()
            status_result = pesapal.get_transaction_status(order_tracking_id)

            logger.info("[IPN] Pesapal reports status='%s' amount=%s for TrackingId=%s",
                        status_result.payment_status_description, status_result.amount, order_tracking_id)

            result = services.payment.payment.handle_pesapal_ipn(
                tracking_id=order_tracking_id,
                status_result=status_result,
            )
            return jsonify({"response": "OK", "status": result.get("status")}), 200

        except Exception as e:
            logger.error("[IPN] Unhandled exception: %r", e)
            if services is not None:
                services._repos.session.rollback()
            return jsonify({"response": "ERR", "message": "Internal processing error"}), 200
