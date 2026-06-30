import logging
from dataclasses import asdict
from typing import Any

from flask import request
from flask.views import MethodView
from flask_login import login_required, current_user
from marshmallow import ValidationError as MarshmallowValidationError

from tuned.core.logging import get_logger
from tuned.utils.responses import success_response, error_response
from tuned.utils.dependencies import get_services
from tuned.utils.auth import get_user_ip, get_user_agent
from tuned.utils.decorators import admin_required
from tuned.core.exceptions import NotFound, ValidationError as CoreValidationError

from tuned.apis.order_deliveries.schemas.delivery import UpdateOrderDeliveryStatusSchema
from tuned.dtos.order_delivery import UpdateOrderDeliveryStatusDTO

logger: logging.Logger = get_logger(__name__)

class CreateDeliveryView(MethodView):
    decorators = [login_required, admin_required]

    def post(self, order_id: str) -> tuple[Any, int]:
        try:
            user_id = current_user.id
            
            delivery_files = request.files.getlist('delivery_files')
            plagiarism_reports = request.files.getlist('plagiarism_reports')

            has_delivery = delivery_files and any(f.filename for f in delivery_files)
            has_plagiarism = plagiarism_reports and any(f.filename for f in plagiarism_reports)

            if not has_delivery and not has_plagiarism:
                logger.error("No files provided for delivery")
                return error_response(message="No files provided", status=400)

            ip_address = get_user_ip() or "127.0.0.1"
            user_agent = get_user_agent() or request.user_agent.string

            response_dto = get_services().order_delivery.create_delivery(
                order_id=order_id,
                delivery_files=delivery_files if has_delivery else [],
                plagiarism_reports=plagiarism_reports if has_plagiarism else [],
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            return success_response(
                data=asdict(response_dto),
                message="Delivery created successfully",
                status=201
            )
        except NotFound as e:
            logger.error(f"Failed to create delivery: {e}")
            return error_response(message="Failed to create delivery. Resource not found.", status=404)
        except CoreValidationError as e:
            logger.error(f"Failed to create delivery: {e}")
            return error_response(message="Failed to create delivery. Invalid data.", status=400)
        except Exception as e:
            logger.error(f"Failed to create delivery: {e}")
            return error_response(message="Failed to create delivery. Server error.", status=500)


class GetOrderDeliveriesView(MethodView):
    decorators = [login_required]

    def get(self, order_id: str) -> tuple[Any, int]:
        try:
            services = get_services()
            order = services._repos.order.get_by_id(order_id)
            if not order:
                logger.error(f"Failed to fetch deliveries: {e}")
                return error_response(message="Failed to fetch deliveries. Resource not found.", status=404)

            # Access check: Admin or client owning the order
            if not current_user.is_admin and str(order.client_id) != str(current_user.id):
                logger.error(f"Failed to fetch deliveries: {e}")
                return error_response(message="Failed to fetch deliveries. Forbidden.", status=403)

            deliveries = services.order_delivery.get_deliveries_by_order(order_id)
            return success_response(
                data=[asdict(d) for d in deliveries],
                message="Deliveries fetched successfully",
                status=200
            )
        except NotFound as e:
            logger.error(f"Failed to fetch deliveries: {e}")
            return error_response(message="Failed to fetch deliveries. Resource not found.", status=404)
        except Exception as e:
            logger.error(f"Failed to fetch deliveries: {e}")
            return error_response(message="Failed to fetch deliveries. Server error.", status=500)


class GetDeliveryByIdView(MethodView):
    decorators = [login_required]

    def get(self, delivery_id: str) -> tuple[Any, int]:
        try:
            services = get_services()
            delivery = services.order_delivery.get_delivery_by_id(delivery_id)
            if not delivery:
                logger.error(f"Failed to fetch delivery: {e}")
                return error_response(message="Failed to fetch delivery. Resource not found.", status=404)

            # Access check: Admin or client owning the order
            order = services._repos.order.get_by_id(str(delivery.order_id))
            if not order:
                logger.error(f"Failed to fetch delivery: {e}")
                return error_response(message="Failed to fetch delivery. Resource not found.", status=404)

            if not current_user.is_admin and str(order.client_id) != str(current_user.id):
                return error_response(message="Forbidden: Access denied", status=403)

            return success_response(
                data=asdict(delivery),
                message="Delivery fetched successfully",
                status=200
            )
        except NotFound as e:
            logger.error(f"Failed to fetch delivery: {e}")
            return error_response(message="Failed to fetch delivery. Resource not found.", status=404)
        except Exception as e:
            logger.error(f"Failed to fetch delivery: {e}")
            return error_response(message="Failed to fetch delivery. Server error.", status=500)


class AddDeliveryFilesView(MethodView):
    decorators = [login_required, admin_required]

    def post(self, delivery_id: str) -> tuple[Any, int]:
        try:
            user_id = current_user.id
            
            delivery_files = request.files.getlist('delivery_files')
            plagiarism_reports = request.files.getlist('plagiarism_reports')

            has_delivery = delivery_files and any(f.filename for f in delivery_files)
            has_plagiarism = plagiarism_reports and any(f.filename for f in plagiarism_reports)

            if not has_delivery and not has_plagiarism:
                logger.error("No files provided to add")
                return error_response(message="No files provided", status=400)

            delivery = get_services().order_delivery.get_delivery_by_id(delivery_id)
            if not delivery:
                logger.error(f"Failed to add delivery files: {e}")
                return error_response(message="Failed to add delivery files. Resource not found.", status=404)

            ip_address = get_user_ip() or "127.0.0.1"
            user_agent = get_user_agent() or request.user_agent.string

            response_dto = get_services().order_delivery.add_delivery_files(
                delivery_id=delivery_id,
                order_id=delivery.order_id,
                delivery_files=delivery_files if has_delivery else [],
                plagiarism_reports=plagiarism_reports if has_plagiarism else [],
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            return success_response(
                data=asdict(response_dto),
                message="Files added successfully",
                status=200
            )
        except NotFound as e:
            logger.error(f"Failed to add delivery files: {e}")
            return error_response(message="Failed to add delivery files. Resource not found.", status=404)
        except CoreValidationError as e:
            logger.error(f"Failed to add delivery files: {e}")
            return error_response(message="Failed to add delivery files. Invalid data.", status=400)
        except Exception as e:
            logger.error(f"Failed to add delivery files: {e}")
            return error_response(message="Failed to add delivery files. Server error.", status=500)


class UpdateDeliveryStatusView(MethodView):
    decorators = [login_required, admin_required]

    def patch(self, delivery_id: str) -> tuple[Any, int]:
        try:
            data = request.get_json()
            if not data:
                return error_response(message="No input data provided", status=400)

            try:
                schema_data = UpdateOrderDeliveryStatusSchema().load(data)
                dto = UpdateOrderDeliveryStatusDTO(**schema_data)
            except MarshmallowValidationError as err:
                logger.error(f"Validation failed: {err}")
                return error_response(message="Validation failed", status=400)

            user_id = current_user.id
            ip_address = get_user_ip() or "127.0.0.1"
            user_agent = get_user_agent() or request.user_agent.string

            response_dto = get_services().order_delivery.update_delivery_status(
                delivery_id=delivery_id,
                dto=dto,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            return success_response(
                data=asdict(response_dto),
                message="Delivery status updated successfully",
                status=200
            )
        except NotFound as e:
            logger.error(f"Failed to update delivery status: {e}")
            return error_response(message="Failed to update delivery status. Resource not found.", status=404)
        except CoreValidationError as e:
            logger.error(f"Failed to update delivery status: {e}")
            return error_response(message="Failed to update delivery status. Invalid data.", status=400)
        except Exception as e:
            logger.error(f"Failed to update delivery status: {e}")
            return error_response(message="Failed to update delivery status", status=500)


class MarkClientNotifiedView(MethodView):
    decorators = [login_required, admin_required]

    def patch(self, delivery_id: str) -> tuple[Any, int]:
        try:
            response_dto = get_services().order_delivery.mark_client_notified(delivery_id)
            return success_response(
                data=asdict(response_dto),
                message="Client marked as notified successfully",
                status=200
            )
        except NotFound as e:
            logger.error(f"Failed to mark client as notified: {e}")
            return error_response(message="Failed to mark client as notified. Resource not found.", status=404)
        except CoreValidationError as e:
            logger.error(f"Failed to mark client as notified: {e}")
            return error_response(message="Failed to mark client as notified. Invalid data.", status=400)
        except Exception as e:
            logger.error(f"Failed to mark client as notified: {e}")
            return error_response(message="Failed to mark client as notified. Server error.", status=500)


class DeleteDeliveryView(MethodView):
    decorators = [login_required, admin_required]

    def delete(self, delivery_id: str) -> tuple[Any, int]:
        try:
            user_id = current_user.id
            ip_address = get_user_ip() or "127.0.0.1"
            user_agent = get_user_agent() or request.user_agent.string

            get_services().order_delivery.delete_delivery(
                delivery_id=delivery_id,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            return success_response(
                data={},
                message="Delivery deleted successfully",
                status=200
            )
        except NotFound as e:
            logger.error(f"Failed to delete delivery: {e}")
            return error_response(message="Failed to delete delivery. Resource not found.", status=404)
        except CoreValidationError as e:
            logger.error(f"Failed to delete delivery: {e}")
            return error_response(message="Failed to delete delivery. Invalid data.", status=400)
        except Exception as e:
            logger.error(f"Failed to delete delivery: {e}")
            return error_response(message="Failed to delete delivery", status=500)
