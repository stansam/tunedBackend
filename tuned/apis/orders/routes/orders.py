from tuned.utils import success_response
from flask_login import login_required, current_user
from flask import request
from flask.views import MethodView
from dataclasses import asdict
from marshmallow import ValidationError
import logging
from tuned.utils.responses import error_response
from tuned.utils.decorators import rate_limit
from tuned.apis.orders.schemas.order import(
    CreateOrderSchema, ValidateDiscountSchema,
    SaveDraftSchema, OrderListRequestSchema,
    OrderCommentCreateSchema, OrderCommentUpdateSchema
)
from tuned.core.logging import get_logger
from tuned.utils.auth import get_user_ip, get_user_agent
from tuned.utils.dependencies import get_services

logger: logging.Logger = get_logger(__name__)

class CreateOrderView(MethodView):
    decorators = [login_required]
    def post(self):
        try:
            user_id = current_user.id
            data = request.get_json()
            if not data:
                logger.error(f"No input data provided")
                return error_response(message="No input data provided", status=400)
            
            try:
                dto = CreateOrderSchema().load(data)
            except ValidationError as err:
                logger.error(f"Validation failed: {err}")
                return error_response(message="Validation failed", status=400)

            ip_address = get_user_ip() or "127.0.0.1"
            user_agent = get_user_agent() or request.user_agent.string

            try:
                response_dto = get_services().order.create_order(dto, user_id, ip_address, user_agent)
                return success_response(data=asdict(response_dto), message="Order created successfully", status=201)
            except ValueError as e:
                logger.warning(f"[CreateOrderView] Business rule rejected: {e}")
                return error_response(message="Failed to create order", status=422)
        except Exception as e:
            logger.error(f"Failed to create order: {e}")
            return error_response(message="Failed to create order", status=500)

class ValidateDiscountView(MethodView):
    decorators = [login_required, rate_limit(max_requests=10, window=60, key_prefix='discount_val')]
    def post(self):
        try:
            data = request.get_json()
            if not data:
                logger.error(f"No input data provided")
                return error_response(message="No input data provided", status=400)
            
            try:
                dto = ValidateDiscountSchema().load(data)
            except ValidationError as err:
                logger.error(f"Validation failed: {err}")
                return error_response(message="Validation failed", status=400)

            response_dto = get_services().order.validate_discount(dto.code, dto.subtotal)
            return success_response(data=asdict(response_dto), message="Discount validated successfully", status=200)
        except Exception as e:
            logger.error(f"Failed to validate discount: {e}")
            return error_response(message="Failed to validate discount", status=500)

class UploadOrderFilesView(MethodView):
    decorators = [login_required]
    def post(self, order_id):
        try:
            user_id = current_user.id
            is_admin = current_user.is_admin
            if 'files' not in request.files:
                logger.error(f"No files provided")
                return error_response(message="No files provided", status=400)

            files = request.files.getlist('files')
            if not files or all(f.filename == '' for f in files):
                logger.error(f"No files selected")
                return error_response(message="No files selected", status=400)

            ip_address = get_user_ip() or "127.0.0.1"
            user_agent = get_user_agent() or request.user_agent.string

            response_dto = get_services().order.upload_order_files(order_id, user_id, files, is_admin, ip_address, user_agent)
            return success_response(data=asdict(response_dto), message="Files uploaded successfully", status=200)
        except Exception as e:
            logger.error(f"Failed to upload files: {e}")
            return error_response(message="Failed to upload files", status=500)

class SaveDraftView(MethodView):
    decorators = [login_required]
    def post(self):
        try:
            user_id = current_user.id
            data = request.get_json()
            if not data:
                logger.error(f"No input data provided")
                return error_response(message="No input data provided", status=400)
            
            try:
                dto = SaveDraftSchema().load(data)
                dto.user_id = user_id
            except ValidationError as err:
                logger.error(f"Validation failed: {err}")
                return error_response(message="Validation failed", status=400)

            ip_address = get_user_ip() or "127.0.0.1"
            user_agent = get_user_agent() or request.user_agent.string
            response_dto = get_services().order.save_draft(dto, ip_address=ip_address, user_agent=user_agent)
            return success_response(data=asdict(response_dto), message="Draft saved successfully", status=200)
        except Exception as e:
            logger.error(f"Failed to save draft: {e}")
            return error_response(message="Failed to save draft", status=500)

class GetDraftView(MethodView):
    decorators = [login_required]
    def get(self):
        try:
            user_id = current_user.id
            draft = get_services().order.get_draft(user_id)
            if not draft:
                logger.error(f"No draft found for user {user_id}")
                return error_response(message="No draft found", status=404)
            return success_response(data=asdict(draft), message="Draft fetched successfully", status=200)
        except Exception as e:
            logger.error(f"Failed to fetch draft: {e}")
            return error_response(message="Failed to fetch draft", status=500)

class ListClientOrders(MethodView):
    decorators = [login_required]
    def post(self):
        try:
            user_id = current_user.id
            data = request.get_json()
            if not data:
                logger.error(f"No input data provided")
                return error_response(message="No input data provided", status=400)
            
            try:
                dto = OrderListRequestSchema().load(data)
            except ValidationError as err:
                logger.error(f"Validation failed: {err}")
                return error_response(message="Validation failed", status=400)

            response_dto = get_services().order.list_client_orders(user_id, dto)
            return success_response(data=asdict(response_dto), message="Orders fetched successfully", status=200)
        except Exception as e:
            logger.exception(f"Failed to fetch orders: {e}")
            return error_response(message="Failed to fetch orders", status=500)

class GetOrderView(MethodView):
    decorators = [login_required]
    def get(self, order_number: str):
        try:
            user_id = current_user.id
            response_dto = get_services().order.get_client_order_details_by_order_number(order_number, user_id)
            return success_response(data=asdict(response_dto), message="Order fetched successfully", status=200)
        except Exception as e:
            logger.error(f"Failed to fetch order: {e}")
            return error_response(message="Failed to fetch order", status=500)

class GetOrderByIdView(MethodView):
    decorators = [login_required]
    def get(self, order_id: str):
        try:
            user_id = current_user.id
            response_dto = get_services().order.get_client_order_details_by_id(order_id, user_id)
            return success_response(data=asdict(response_dto), message="Order fetched successfully", status=200)
        except Exception as e:
            logger.error(f"Failed to fetch order by ID: {e}")
            return error_response(message="Failed to fetch order", status=500)


class ListOrderCommentsView(MethodView):
    decorators = [login_required]
    def get(self, order_id: str):
        try:
            user_id = current_user.id
            is_admin = current_user.is_admin

            dtos = get_services().order.get_order_comments(order_id, user_id, is_admin)
            return success_response(data=[asdict(d) for d in dtos], message="Comments fetched", status=200)
        except Exception as e:
            logger.error("[ListOrderCommentsView] %s", e)
            return error_response(message="Failed to fetch comments", status=500)

class CreateOrderCommentView(MethodView):
    decorators = [login_required, rate_limit(max_requests=50, window=3600, key_prefix="comment")]
    def post(self, order_id: str):
        try:
            data = request.get_json()
            if not data:
                return error_response(message="No input data", status=400)
            try:
                dto = OrderCommentCreateSchema().load(data)
            except ValidationError as err:
                return error_response(message="Validation failed", status=400)
            ip = get_user_ip() or "127.0.0.1"
            ua = get_user_agent() or request.user_agent.string
            result = get_services().order.create_order_comment(order_id, current_user.id, dto, current_user.is_admin, ip, ua)
            return success_response(data=asdict(result), message="Comment posted", status=201)
        except Exception as e:
            logger.error("[CreateOrderCommentView] %s", e)
            return error_response(message="Failed to post comment", status=500)

class UpdateDeleteOrderCommentView(MethodView):
    decorators = [login_required]
    def patch(self, order_id: str, comment_id: str):
        try:
            data = request.get_json()
            if not data:
                return error_response(message="No input data", status=400)
            try:
                dto = OrderCommentUpdateSchema().load(data)
            except ValidationError as err:
                return error_response(message="Validation failed", status=400)
            result = get_services().order.update_order_comment(order_id, comment_id, current_user.id, dto)
            return success_response(data=asdict(result), message="Comment updated", status=200)
        except Exception as e:
            logger.error("[UpdateDeleteOrderCommentView.patch] %s", e)
            return error_response(message="Failed to update comment", status=500)

    def delete(self, order_id: str, comment_id: str):
        try:
            get_services().order.delete_order_comment(order_id, comment_id, current_user.id)
            return success_response(data={}, message="Comment deleted", status=200)
        except Exception as e:
            logger.error("[UpdateDeleteOrderCommentView.delete] %s", e)
            return error_response(message="Failed to delete comment", status=500)