import logging
import copy
from typing import Optional, List, TYPE_CHECKING
from tuned.dtos.communication import (
    CreateChatDTO, ChatMessageCreateDTO, ChatResponseDTO, ChatMessageResponseDTO, ChatMessagePageDTO
)
from tuned.dtos.user import UserResponseDTO
from tuned.dtos import ActivityLogCreateDTO
from tuned.repository.exceptions import DatabaseError, NotFound, ValidationError
from tuned.core.logging import get_logger
from datetime import datetime, timezone
from tuned.core.events import get_event_bus
from tuned.interface.communication.events import ChatEvents
from tuned.utils.variables import Variables

if TYPE_CHECKING:
    from tuned.repository import Repository
    from tuned.interface import Services

logger: logging.Logger = get_logger(__name__)

class ChatService:
    def __init__(self, repos: "Repository", services: "Services") -> None:
        self._repo = repos.chat
        self._repos = repos
        self._services = services
        self._audit_service = services.audit.activity_log

    def create_chat(self, dto: CreateChatDTO, ip_address: Optional[str] = "system", user_agent: Optional[str] = "system") -> ChatResponseDTO:
        try:
            user = self._repos.user.get_user_by_id(dto.user_id)
            if not user:
                raise ValidationError("User not found")

            if dto.order_id:
                order = self._repos.order.get_by_id(dto.order_id)
                if not order:
                    raise ValidationError("Associated order does not exist")
                if not user.is_admin and str(order.client_id) != str(dto.user_id):
                    raise ValidationError("Not authorized to link this order to chat")

            chat = self._repo.create_chat(dto)

            # Audit log
            try:
                self._audit_service.log(ActivityLogCreateDTO(
                    action=Variables.CHAT_CREATED_ACTION,
                    user_id=dto.user_id,
                    entity_type=Variables.CHAT_ENTITY_TYPE,
                    entity_id=str(chat.id),
                    before=None,
                    after=chat,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    created_by=dto.user_id
                ))
            except Exception as e:
                logger.error("[ChatService.create_chat] Audit log failed: %r", e)

            self._repo.save()
            
            try:
                get_event_bus().emit(ChatEvents.CHAT_CREATED, {
                    "chat_id": str(chat.id),
                    "user_id": str(chat.user_id),
                    "subject": chat.subject,
                    "order_id": str(chat.order_id) if chat.order_id else None,
                    "created_at": chat.created_at.isoformat() if chat.created_at else datetime.now(timezone.utc).isoformat()
                })
            except Exception as e:
                logger.error("[ChatService.create_chat] Event emit failed: %r", e)

            return ChatResponseDTO.from_model(chat, include_messages=False)
        except Exception as e:
            self._repo.rollback()
            logger.error("[ChatService.create_chat] Failed: %r", e)
            raise

    def get_chat_details(self, chat_id: str, user_id: str, is_admin: bool = False) -> ChatResponseDTO:
        chat = self._repo.get_chat_for_user(chat_id, user_id, is_admin)
        if not chat:
            raise NotFound("Chat room not found")
        
        return ChatResponseDTO.from_model(chat, current_user_id=user_id, include_messages=False)

    def list_client_chats(self, user_id: str) -> List[ChatResponseDTO]:
        chats = self._repo.list_client_chats(user_id)
        unread_counts = self._repo.get_unread_counts_for_user(user_id)
        return [
            ChatResponseDTO.from_model(
                c, 
                current_user_id=user_id, 
                include_messages=False, 
                unread_count=unread_counts.get(str(c.id), 0)
            ) for c in chats
        ]

    def list_all_chats_admin(self, acting_admin_id: Optional[str] = None) -> List[ChatResponseDTO]:
        chats = self._repo.list_all_chats_admin()
        unread_counts = {}
        if acting_admin_id:
            unread_counts = self._repo.get_unread_counts_for_user(acting_admin_id)
        return [
            ChatResponseDTO.from_model(
                c, 
                current_user_id=acting_admin_id, 
                include_messages=False, 
                unread_count=unread_counts.get(str(c.id), 0) if acting_admin_id else None
            ) for c in chats
        ]

    def send_message(self, dto: ChatMessageCreateDTO, is_admin: bool = False, ip_address: Optional[str] = "system", user_agent: Optional[str] = "system") -> ChatMessageResponseDTO:
        try:
            chat = self._repo.get_by_id(dto.chat_id)
            if not chat:
                raise NotFound("Chat room not found")

            from tuned.models.enums import ChatStatus
            if chat.status == ChatStatus.CLOSED:
                raise ValidationError("Chat is closed")

            if not is_admin and str(chat.user_id) != str(dto.user_id):
                raise ValidationError("Not authorized to send messages to this chat")

            msg = self._repo.create_message(dto.chat_id, dto.user_id, dto.content)

            # Audit log
            try:
                self._audit_service.log(ActivityLogCreateDTO(
                    action=Variables.CHAT_MESSAGE_SENT_ACTION,
                    user_id=dto.user_id,
                    entity_type=Variables.CHAT_MESSAGE_ENTITY_TYPE,
                    entity_id=str(msg.id),
                    before=None,
                    after=msg,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    created_by=dto.user_id
                ))
            except Exception as e:
                logger.error("[ChatService.send_message] Audit log failed: %r", e)

            self._repo.save()

            recipient_id = chat.user_id if is_admin else chat.admin_id
            
            try:
                get_event_bus().emit(ChatEvents.MESSAGE_SENT, {
                    "sender_id": str(dto.user_id),
                    "recipient_id": str(recipient_id) if recipient_id else None,
                    "chat_id": str(dto.chat_id),
                    "message_id": str(msg.id),
                    "content": dto.content,
                    "is_admin": is_admin,
                    "created_at": msg.created_at.isoformat() if msg.created_at else datetime.now(timezone.utc).isoformat()
                })
            except Exception as e:
                logger.error("[ChatService.send_message] Event emit failed: %r", e)

            return ChatMessageResponseDTO.from_model(msg)
        except Exception as e:
            self._repo.rollback()
            logger.error("[ChatService.send_message] Failed: %r", e)
            raise

    def assign_support_agent(self, chat_id: str, admin_id: str, acting_admin_id: str, ip_address: Optional[str] = "system", user_agent: Optional[str] = "system") -> ChatResponseDTO:
        try:
            admin_user = self._repos.user.get_user_by_id(admin_id)
            if not admin_user or not admin_user.is_admin:
                raise ValidationError("Assigned user must be an administrator")

            before_chat = self._repo.get_by_id(chat_id)
            before_snapshot = copy.deepcopy(before_chat) if before_chat else None

            chat = self._repo.assign_admin(chat_id, admin_id)
            # Audit log
            try:
                self._audit_service.log(ActivityLogCreateDTO(
                    action=Variables.CHAT_ASSIGNED_ACTION,
                    user_id=acting_admin_id,
                    entity_type=Variables.CHAT_ENTITY_TYPE,
                    entity_id=str(chat.id),
                    before=before_snapshot,
                    after=chat,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    created_by=acting_admin_id
                ))
            except Exception as e:
                logger.error("[ChatService.assign_support_agent] Audit log failed: %r", e)

            self._repo.save()
            
            try:
                get_event_bus().emit(ChatEvents.ASSIGNED, {
                    "chat_id": str(chat.id),
                    "user_id": str(chat.user_id),
                    "admin_id": admin_id,
                    "assigned_by": acting_admin_id
                })
            except Exception as e:
                logger.error("[ChatService.assign_support_agent] Event emit failed: %r", e)

            return ChatResponseDTO.from_model(chat, include_messages=False)
        except Exception as e:
            self._repo.rollback()
            logger.error("[ChatService.assign_support_agent] Failed: %r", e)
            raise

    def change_chat_status(self, chat_id: str, status: str, acting_user_id: str, ip_address: Optional[str] = "system", user_agent: Optional[str] = "system") -> ChatResponseDTO:
        try:
            from tuned.models.enums import ChatStatus
            try:
                status_enum = ChatStatus(status)
            except ValueError:
                raise ValidationError(f"Invalid status: {status}")

            chat = self._repo.get_by_id(chat_id)
            if not chat:
                raise NotFound("Chat room not found")

            before_snapshot = copy.deepcopy(chat)
            old_status = chat.status.value if hasattr(chat.status, 'value') else str(chat.status)
            updated_chat = self._repo.update_status(chat_id, status_enum)
            # Audit log
            try:
                self._audit_service.log(ActivityLogCreateDTO(
                    action=Variables.CHAT_STATUS_CHANGED_ACTION,
                    user_id=acting_user_id,
                    entity_type=Variables.CHAT_ENTITY_TYPE,
                    entity_id=str(updated_chat.id),
                    before=before_snapshot,
                    after=updated_chat,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    created_by=acting_user_id
                ))
            except Exception as e:
                logger.error("[ChatService.change_chat_status] Audit log failed: %r", e)
                
            self._repo.save()
            
            try:
                get_event_bus().emit(ChatEvents.STATUS_CHANGED, {
                    "chat_id": str(updated_chat.id),
                    "user_id": str(updated_chat.user_id),
                    "new_status": status,
                    "old_status": old_status,
                    "changed_by": acting_user_id
                })
            except Exception as e:
                logger.error("[ChatService.change_chat_status] Event emit failed: %r", e)

            return ChatResponseDTO.from_model(updated_chat, include_messages=False)
        except Exception as e:
            self._repo.rollback()
            logger.error("[ChatService.change_chat_status] Failed: %r", e)
            raise

    def mark_chat_as_read(self, chat_id: str, user_id: str, is_admin: bool = False) -> int:
        try:
            chat = self._repo.get_chat_for_user(chat_id, user_id, is_admin)
            if not chat:
                raise NotFound("Chat room not found")
            marked = self._repo.mark_as_read(chat_id, user_id)
            if marked:
                self._repo.save()
                recipient_id = chat.admin_id if not is_admin else chat.user_id
                try:
                    get_event_bus().emit(ChatEvents.MESSAGE_READ, {
                        "chat_id": chat_id,
                        "reader_id": user_id,
                        "recipient_id": str(recipient_id) if recipient_id else None,
                        "message_ids": [str(m.id) for m in marked]
                    })
                except Exception as e:
                    logger.error("[ChatService.mark_chat_as_read] Read receipt emit failed: %r", e)
            return len(marked)
        except Exception as e:
            self._repo.rollback()
            logger.error("[ChatService.mark_chat_as_read] Failed: %r", e)
            raise

    def edit_message(self, chat_id: str, message_id: str, content: str, user_id: str, is_admin: bool = False, ip_address: Optional[str] = "system", user_agent: Optional[str] = "system") -> ChatMessageResponseDTO:
        try:
            chat = self._repo.get_by_id(chat_id)
            if not chat:
                raise NotFound("Chat room not found")

            msg = self._repo.get_message_by_id(message_id)
            if not msg:
                raise NotFound("Message not found")

            if str(msg.chat_id) != str(chat_id):
                raise ValidationError("Message does not belong to this chat")

            if str(msg.user_id) != str(user_id):
                raise ValidationError("Not authorized to edit this message")

            updated_msg = self._repo.update_message_content(message_id, content)

            # Audit log
            try:
                self._audit_service.log(ActivityLogCreateDTO(
                    action=Variables.CHAT_MESSAGE_EDITED_ACTION,
                    user_id=user_id,
                    entity_type=Variables.CHAT_MESSAGE_ENTITY_TYPE,
                    entity_id=str(msg.id),
                    before=msg,
                    after=updated_msg,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    created_by=user_id
                ))
            except Exception as e:
                logger.error("[ChatService.edit_message] Audit log failed: %r", e)
                
            self._repo.save()
            
            recipient_id = chat.user_id if is_admin else chat.admin_id

            try:
                get_event_bus().emit(ChatEvents.MESSAGE_EDITED, {
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "recipient_id": str(recipient_id) if recipient_id else None,
                    "content": content,
                    "updated_at": updated_msg.updated_at.isoformat() if updated_msg.updated_at else datetime.now(timezone.utc).isoformat()
                })
            except Exception as e:
                logger.error("[ChatService.edit_message] Event emit failed: %r", e)

            return ChatMessageResponseDTO.from_model(updated_msg)
        except Exception as e:
            self._repo.rollback()
            logger.error("[ChatService.edit_message] Failed: %r", e)
            raise

    def delete_message(self, chat_id: str, message_id: str, user_id: str, is_admin: bool = False, ip_address: Optional[str] = "system", user_agent: Optional[str] = "system") -> None:
        try:
            chat = self._repo.get_by_id(chat_id)
            if not chat:
                raise NotFound("Chat room not found")

            msg = self._repo.get_message_by_id(message_id)
            if not msg:
                raise NotFound("Message not found")

            if str(msg.chat_id) != str(chat_id):
                raise ValidationError("Message does not belong to this chat")

            if not is_admin and str(msg.user_id) != str(user_id):
                raise ValidationError("Not authorized to delete this message")

            updated_msg = self._repo.delete_message(message_id, user_id)
            # Audit log
            try:
                self._audit_service.log(ActivityLogCreateDTO(
                    action=Variables.CHAT_MESSAGE_DELETED_ACTION,
                    user_id=user_id,
                    entity_type=Variables.CHAT_MESSAGE_ENTITY_TYPE,
                    entity_id=str(msg.id),
                    before=msg,
                    after=updated_msg,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    created_by=user_id
                ))
            except Exception as e:
                logger.error("[ChatService.delete_message] Audit log failed: %r", e)
                
            self._repo.save()
            
            recipient_id = chat.user_id if is_admin else chat.admin_id

            try:
                get_event_bus().emit(ChatEvents.MESSAGE_DELETED, {
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "recipient_id": str(recipient_id) if recipient_id else None
                })
            except Exception as e:
                logger.error("[ChatService.delete_message] Event emit failed: %r", e)

        except Exception as e:
            self._repo.rollback()
            logger.error("[ChatService.delete_message] Failed: %r", e)
            raise

    def get_messages(self, chat_id: str, user_id: str, is_admin: bool = False, before_id: Optional[str] = None, limit: int = 50) -> ChatMessagePageDTO:
        chat = self._repo.get_chat_for_user(chat_id, user_id, is_admin)
        if not chat:
            raise NotFound("Chat room not found")
        
        # Fetch limit + 1 to see if we have more
        messages = self._repo.get_messages_paginated(chat_id, before_id, limit + 1)
        has_more = len(messages) > limit
        if has_more:
            messages = messages[1:]
            
        messages_dto = [ChatMessageResponseDTO.from_model(m) for m in messages]
        next_cursor = messages_dto[0].id if (has_more and messages_dto) else None
        
        return ChatMessagePageDTO(
            messages=messages_dto,
            has_more=has_more,
            next_cursor=next_cursor
        )

    def list_support_agents(self) -> List[UserResponseDTO]:
        try:
            agents = self._repos.user.get_admin_users()
            return [UserResponseDTO.from_model(a) for a in agents]
        except Exception as e:
            logger.error("[ChatService.list_support_agents] Failed: %r", e)
            raise
