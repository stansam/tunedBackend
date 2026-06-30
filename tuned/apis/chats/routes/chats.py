from flask import request
from flask.views import MethodView
from flask_login import login_required, current_user
from dataclasses import asdict
from marshmallow import ValidationError
import logging
from tuned.utils.responses import success_response, error_response, validation_error_response
from tuned.utils.decorators import admin_required
from tuned.utils.dependencies import get_services
from tuned.repository.exceptions import NotFound, ValidationError as RepoValidationError
from tuned.core.logging import get_logger
from tuned.utils.auth import get_user_ip, get_user_agent
from tuned.utils.rate_limit import socket_rate_limit
from tuned.apis.chats.schemas.chats import (
    CreateChatSchema, SendMessageSchema, AssignAdminSchema, ChangeStatusSchema, EditMessageSchema
)

logger: logging.Logger = get_logger(__name__)

class ListClientChatsView(MethodView):
    decorators = [login_required]

    def get(self):
        try:
            user_id = current_user.id
            chats = get_services().chat.list_client_chats(user_id)
            return success_response(data=[asdict(c) for c in chats], status=200)
        except RepoValidationError as e:
            logger.error("[ListClientChatsView] %s", e)
            return error_response(message="Validation error", status=400)
        except NotFound as e:
            logger.error("[ListClientChatsView] %s", e)
            return error_response(message="Not Found", status=404)
        except Exception as e:
            logger.error("[ListClientChatsView] %s", e)
            return error_response(message="Failed to fetch chats", status=500)

class CreateChatView(MethodView):
    decorators = [login_required]

    def post(self):
        try:
            data = request.get_json()
            if not data:
                return error_response(message="No input data provided", status=400)
            try:
                dto = CreateChatSchema().load(data)
            except ValidationError as err:
                logger.error("[CreateChatView] %s", err)
                return validation_error_response(err.messages)

            dto.user_id = current_user.id
            ip_address = get_user_ip() or "127.0.0.1"
            user_agent = get_user_agent() or request.user_agent.string
            response_dto = get_services().chat.create_chat(dto, ip_address=ip_address, user_agent=user_agent)
            return success_response(data=asdict(response_dto), message="Chat created successfully", status=201)
        except RepoValidationError as e:
            logger.error("[CreateChatView] %s", e)
            return error_response(message="Validation error", status=400)
        except NotFound as e:
            logger.error("[CreateChatView] %s", e)
            return error_response(message="Not Found", status=404)
        except Exception as e:
            logger.error("[CreateChatView] %s", e)
            return error_response(message="Failed to create chat", status=500)

class GetChatDetailsView(MethodView):
    decorators = [login_required]

    def get(self, chat_id):
        try:
            user_id = current_user.id
            is_admin = current_user.is_admin
            response_dto = get_services().chat.get_chat_details(chat_id, user_id, is_admin)
            return success_response(data=asdict(response_dto), status=200)
        except RepoValidationError as e:
            logger.error("[GetChatDetailsView] %s", e)
            return error_response(message="Validation error", status=400)
        except NotFound as e:
            logger.error("[GetChatDetailsView] %s", e)
            return error_response(message="Not Found", status=404)
        except Exception as e:
            logger.error("[GetChatDetailsView] %s", e)
            return error_response(message="Failed to fetch chat details", status=500)

class SendMessageView(MethodView):
    decorators = [login_required]

    def post(self, chat_id):
        try:
            if not socket_rate_limit(f"http:send_message:{current_user.id}", limit=30, window=60):
                logger.error("[SendMessageView] Rate limit exceeded")
                return error_response(message="Rate limit exceeded. Please wait a moment.", status=429)

            data = request.get_json()
            if not data:
                logger.error("[SendMessageView] No input data provided")
                return error_response(message="No input data provided", status=400)
            try:
                dto = SendMessageSchema().load(data)
            except ValidationError as err:
                logger.error("[SendMessageView] %s", err)
                return validation_error_response(err.messages)

            dto.chat_id = chat_id
            dto.user_id = current_user.id
            is_admin = current_user.is_admin

            ip_address = get_user_ip() or "127.0.0.1"
            user_agent = get_user_agent() or request.user_agent.string
            response_dto = get_services().chat.send_message(dto, is_admin, ip_address=ip_address, user_agent=user_agent)
            return success_response(data=asdict(response_dto), message="Message sent successfully", status=201)
        except RepoValidationError as e:
            logger.error("[SendMessageView] %s", e)
            return error_response(message="Validation error", status=400)
        except NotFound as e:
            logger.error("[SendMessageView] %s", e)
            return error_response(message="Not Found", status=404)
        except Exception as e:
            logger.error("[SendMessageView] %s", e)
            return error_response(message="Failed to send message", status=500)

class GetChatMessagesView(MethodView):
    decorators = [login_required]

    def get(self, chat_id):
        try:
            user_id = current_user.id
            is_admin = current_user.is_admin
            before_id = request.args.get("before")
            limit_val = request.args.get("limit", 50, type=int)
            
            response_dto = get_services().chat.get_messages(
                chat_id=chat_id,
                user_id=user_id,
                is_admin=is_admin,
                before_id=before_id,
                limit=limit_val
            )
            return success_response(data=asdict(response_dto), status=200)
        except RepoValidationError as e:
            logger.error("[GetChatMessagesView] %s", e)
            return error_response(message="Validation error", status=400)
        except NotFound as e:
            logger.error("[GetChatMessagesView] %s", e)
            return error_response(message="Not Found", status=404)
        except Exception as e:
            logger.error("[GetChatMessagesView] %s", e)
            return error_response(message="Failed to fetch messages", status=500)

class MarkChatReadView(MethodView):
    decorators = [login_required]

    def post(self, chat_id):
        try:
            user_id = current_user.id
            is_admin = current_user.is_admin
            marked_count = get_services().chat.mark_chat_as_read(chat_id, user_id, is_admin)
            return success_response(data={"marked_count": marked_count}, message="Messages marked read successfully", status=200)
        except RepoValidationError as e:
            logger.error("[MarkChatReadView] %s", e)
            return error_response(message="Validation error", status=400)
        except NotFound as e:
            logger.error("[MarkChatReadView] %s", e)
            return error_response(message="Not Found", status=404)
        except Exception as e:
            logger.error("[MarkChatReadView] %s", e)
            return error_response(message="Failed to mark messages as read", status=500)

class AdminListChatsView(MethodView):
    decorators = [login_required, admin_required]

    def get(self):
        try:
            chats = get_services().chat.list_all_chats_admin(acting_admin_id=current_user.id)
            return success_response(data=[asdict(c) for c in chats], status=200)
        except RepoValidationError as e:
            logger.error("[AdminListChatsView] %s", e)
            return error_response(message="Validation error", status=400)
        except NotFound as e:
            logger.error("[AdminListChatsView] %s", e)
            return error_response(message="Not Found", status=404)
        except Exception as e:
            logger.error("[AdminListChatsView] %s", e)
            return error_response(message="Failed to fetch chats", status=500)

class AdminAssignView(MethodView):
    decorators = [login_required, admin_required]

    def patch(self, chat_id):
        try:
            data = request.get_json()
            if not data:
                return error_response(message="No input data provided", status=400)
            try:
                schema_data = AssignAdminSchema().load(data)
            except ValidationError as err:
                return validation_error_response(err.messages)

            admin_id = str(schema_data["admin_id"])
            acting_admin_id = current_user.id
            ip_address = get_user_ip() or "127.0.0.1"
            user_agent = get_user_agent() or request.user_agent.string
            response_dto = get_services().chat.assign_support_agent(chat_id, admin_id, acting_admin_id, ip_address=ip_address, user_agent=user_agent)
            return success_response(data=asdict(response_dto), message="Admin assigned successfully", status=200)
        except RepoValidationError as e:
            logger.error("[AdminAssignView] %s", e)
            return error_response(message="Validation error", status=400)
        except NotFound as e:
            logger.error("[AdminAssignView] %s", e)
            return error_response(message="Not Found", status=404)
        except Exception as e:
            logger.error("[AdminAssignView] %s", e)
            return error_response(message="Failed to assign admin", status=500)

class AdminStatusView(MethodView):
    decorators = [login_required, admin_required]

    def patch(self, chat_id):
        try:
            data = request.get_json()
            if not data:
                return error_response(message="No input data provided", status=400)
            try:
                schema_data = ChangeStatusSchema().load(data)
            except ValidationError as err:
                return validation_error_response(err.messages)

            status = schema_data["status"]
            acting_user_id = current_user.id
            ip_address = get_user_ip() or "127.0.0.1"
            user_agent = get_user_agent() or request.user_agent.string
            response_dto = get_services().chat.change_chat_status(chat_id, status, acting_user_id, ip_address=ip_address, user_agent=user_agent)
            return success_response(data=asdict(response_dto), message="Chat status updated successfully", status=200)
        except RepoValidationError as e:
            logger.error("[AdminStatusView] %s", e)
            return error_response(message="Validation error", status=400)
        except NotFound as e:
            logger.error("[AdminStatusView] %s", e)
            return error_response(message="Not Found", status=404)
        except Exception as e:
            logger.error("[AdminStatusView] %s", e)
            return error_response(message="Failed to update status", status=500)

class AdminListAgentsView(MethodView):
    decorators = [login_required, admin_required]

    def get(self):
        try:
            agents = get_services().chat.list_support_agents()
            return success_response(data=[asdict(a) for a in agents], status=200)
        except RepoValidationError as e:
            logger.error("[AdminListAgentsView] %s", e)
            return error_response(message="Validation error", status=400)
        except NotFound as e:
            logger.error("[AdminListAgentsView] %s", e)
            return error_response(message="Not Found", status=404)
        except Exception as e:
            logger.error("[AdminListAgentsView] %s", e)
            return error_response(message="Failed to fetch support agents", status=500)

class EditMessageView(MethodView):
    decorators = [login_required]

    def patch(self, chat_id, message_id):
        try:
            data = request.get_json()
            if not data:
                return error_response(message="No input data provided", status=400)
            try:
                validated = EditMessageSchema().load(data)
            except ValidationError as err:
                return validation_error_response(err.messages)

            user_id = current_user.id
            is_admin = current_user.is_admin
            ip_address = get_user_ip() or "127.0.0.1"
            user_agent = get_user_agent() or request.user_agent.string

            response_dto = get_services().chat.edit_message(
                chat_id, message_id, validated["content"], user_id, is_admin,
                ip_address=ip_address, user_agent=user_agent
            )
            return success_response(data=asdict(response_dto), message="Message updated successfully", status=200)
        except RepoValidationError as e:
            logger.error("[EditMessageView] %s", e)
            return error_response(message="Validation error", status=400)
        except NotFound as e:
            logger.error("[EditMessageView] %s", e)
            return error_response(message="Not Found", status=404)
        except Exception as e:
            logger.error("[EditMessageView] %s", e)
            return error_response(message="Failed to update message", status=500)

class DeleteMessageView(MethodView):
    decorators = [login_required]

    def delete(self, chat_id, message_id):
        try:
            user_id = current_user.id
            is_admin = current_user.is_admin
            ip_address = get_user_ip() or "127.0.0.1"
            user_agent = get_user_agent() or request.user_agent.string

            get_services().chat.delete_message(
                chat_id, message_id, user_id, is_admin,
                ip_address=ip_address, user_agent=user_agent
            )
            return success_response(data={"success": True}, message="Message deleted successfully", status=200)
        except RepoValidationError as e:
            logger.error("[DeleteMessageView] %s", e)
            return error_response(message="Validation error", status=400)
        except NotFound as e:
            logger.error("[DeleteMessageView] %s", e)
            return error_response(message="Not Found", status=404)
        except Exception as e:
            logger.error("[DeleteMessageView] %s", e)
            return error_response(message="Failed to delete message", status=500)

class UploadAttachmentView(MethodView):
    decorators = [login_required]

    def post(self, chat_id):
        try:
            if not socket_rate_limit(f"http:upload_attachment:{current_user.id}", limit=5, window=60):
                logger.error("[UploadAttachmentView] Rate limit exceeded")
                return error_response(message="Rate limit exceeded. Please wait a moment.", status=429)

            get_services().chat.get_chat_details(chat_id, current_user.id, current_user.is_admin)

            if 'file' not in request.files:
                logger.error("[UploadAttachmentView] No file uploaded")
                return error_response('No file uploaded', status=400)

            file = request.files['file']
            if file.filename == '':
                logger.error("[UploadAttachmentView] No file selected")
                return error_response('No file selected', status=400)

            ALLOWED_EXTENSIONS = {
                'docx', 'pdf', 'jpg', 'jpeg', 'png', 'txt', 'doc', 
                'xls', 'xlsx', 'csv', 'ppt', 'pptx', 'mp3', 'wav', 'ogg', 'webm'
            }
            filename = file.filename
            if filename is None:
                logger.error("[UploadAttachmentView] No file name provided")
                return error_response('No file name provided', status=400)

            if '.' not in filename or filename.rsplit('.', 1)[1].lower() not in ALLOWED_EXTENSIONS:
                logger.error("[UploadAttachmentView] File extension not allowed")
                return error_response('File extension not allowed', status=400)

            file.seek(0, 2)
            size = file.tell()
            file.seek(0)
            if size > 25 * 1024 * 1024:
                logger.error("[UploadAttachmentView] File size exceeds maximum allowed (25MB)")
                return error_response('File size exceeds maximum allowed (25MB)', status=400)

            from tuned.models.enums import AssetOwnerType
            owner_id = chat_id
            result = get_services().media.upload_file(
                file=file,
                owner_type=AssetOwnerType.CHAT_MESSAGE,
                owner_id=owner_id,
                is_public=False
            )
            return success_response(data=asdict(result), message="File uploaded successfully", status=201)
        except RepoValidationError as e:
            logger.error("[UploadAttachmentView] %s", e)
            return error_response(message="Validation error", status=400)
        except NotFound as e:
            logger.error("[UploadAttachmentView] %s", e)
            return error_response(message="Not Found", status=404)
        except Exception as e:
            logger.error(f'Chat attachment upload error: {str(e)}')
            return error_response('Failed to upload attachment', status=500)
