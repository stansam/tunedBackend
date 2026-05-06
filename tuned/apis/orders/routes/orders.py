from tuned.utils import success_response
from flask_login import login_required, current_user
from flask import Blueprint, request, jsonify
from flask.views import MethodView
from dataclasses import asdict
from marshmallow import ValidationError
import logging
from tuned.utils.responses import error_response
from tuned.apis.orders.schemas.order import CreateOrderSchema, ValidateDiscountSchema, SaveDraftSchema
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
                logger.error(f"Failed to create order: {e}")
                return error_response(message="Failed to create order", status=400)
        except Exception as e:
            logger.error(f"Failed to create order: {e}")
            return error_response(message="Failed to create order", status=500)

class ValidateDiscountView(MethodView):
    decorators = [login_required]
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
            if 'files' not in request.files:
                logger.error(f"No files provided")
                return error_response(message="No files provided", status=400)

            files = request.files.getlist('files')
            if not files or all(f.filename == '' for f in files):
                logger.error(f"No files selected")
                return error_response(message="No files selected", status=400)

            ip_address = get_user_ip() or "127.0.0.1"
            user_agent = get_user_agent() or request.user_agent.string

            response_dto = get_services().order.upload_order_files(order_id, user_id, files, ip_address, user_agent)
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

            response_dto = get_services().order.save_draft(dto)
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



