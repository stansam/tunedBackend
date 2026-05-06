from flask import Blueprint, request, jsonify
from flask.views import MethodView
from flask_jwt_extended import jwt_required, get_jwt_identity
from tuned.apis.orders.schemas.order import CreateOrderSchema, ValidateDiscountSchema, SaveDraftSchema
from tuned.apis.core import handle_exceptions, inject_services
from marshmallow import ValidationError
from dataclasses import asdict

orders_bp = Blueprint("orders", __name__, url_prefix="/orders")

class CreateOrderView(MethodView):
    @jwt_required()
    @inject_services
    @handle_exceptions
    def post(self, services):
        user_id = get_jwt_identity()
        data = request.get_json()
        if not data:
            return jsonify({"error": "No input data provided"}), 400
        
        try:
            dto = CreateOrderSchema().load(data)
        except ValidationError as err:
            return jsonify(err.messages), 400

        ip_address = request.remote_addr or "127.0.0.1"
        user_agent = request.user_agent.string

        try:
            response_dto = services.order.create_order(dto, user_id, ip_address, user_agent)
            return jsonify(asdict(response_dto)), 201
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

class ValidateDiscountView(MethodView):
    @jwt_required()
    @inject_services
    @handle_exceptions
    def post(self, services):
        data = request.get_json()
        if not data:
            return jsonify({"error": "No input data provided"}), 400
        
        try:
            dto = ValidateDiscountSchema().load(data)
        except ValidationError as err:
            return jsonify(err.messages), 400

        response_dto = services.order.validate_discount(dto.code, dto.subtotal)
        return jsonify(asdict(response_dto)), 200

class UploadOrderFilesView(MethodView):
    @jwt_required()
    @inject_services
    @handle_exceptions
    def post(self, order_id, services):
        user_id = get_jwt_identity()
        if 'files' not in request.files:
            return jsonify({"error": "No files provided"}), 400

        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
             return jsonify({"error": "No files selected"}), 400

        ip_address = request.remote_addr or "127.0.0.1"
        user_agent = request.user_agent.string

        response_dto = services.order.upload_order_files(order_id, user_id, files, ip_address, user_agent)
        return jsonify(asdict(response_dto)), 200

class SaveDraftView(MethodView):
    @jwt_required()
    @inject_services
    @handle_exceptions
    def post(self, services):
        user_id = get_jwt_identity()
        data = request.get_json()
        if not data:
            return jsonify({"error": "No input data provided"}), 400
        
        try:
            dto = SaveDraftSchema().load(data)
            dto.user_id = user_id
        except ValidationError as err:
            return jsonify(err.messages), 400

        response_dto = services.order.save_draft(dto)
        return jsonify(asdict(response_dto)), 200

    @jwt_required()
    @inject_services
    @handle_exceptions
    def get(self, services):
        user_id = get_jwt_identity()
        draft = services.order.get_draft(user_id)
        if not draft:
            return jsonify({"message": "No draft found"}), 404
        return jsonify(asdict(draft)), 200

orders_bp.add_url_rule("/", view_func=CreateOrderView.as_view("create_order"))
orders_bp.add_url_rule("/validate-discount", view_func=ValidateDiscountView.as_view("validate_discount"))
orders_bp.add_url_rule("/<string:order_id>/upload-files", view_func=UploadOrderFilesView.as_view("upload_files"))
orders_bp.add_url_rule("/draft", view_func=SaveDraftView.as_view("draft"))
