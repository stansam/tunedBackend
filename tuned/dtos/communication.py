from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING, List
from tuned.dtos.base import BaseDTO
from tuned.dtos.media import MediaAssetResponseDTO

if TYPE_CHECKING:
    from tuned.models.communication import NewsletterSubscriber, Chat, ChatMessage

@dataclass
class NewsletterSubscribeDTO(BaseDTO):
    email: str
    name: Optional[str] = None
    client_id: Optional[str] = None

@dataclass(kw_only=True)
class NewsletterSubscriberResponseDTO(BaseDTO):
    id: str
    email: str
    name: str
    is_active: bool

    @classmethod
    def from_model(cls, obj: "NewsletterSubscriber") -> "NewsletterSubscriberResponseDTO":
        return cls(
            id=str(obj.id),
            email=obj.email,
            name=obj.name or "",
            is_active=obj.is_active,
            created_at=obj.created_at
        )

@dataclass
class CreateChatDTO(BaseDTO):
    user_id: str
    subject: Optional[str] = None
    order_id: Optional[str] = None

@dataclass
class ChatMessageCreateDTO(BaseDTO):
    chat_id: str
    user_id: str
    content: str

@dataclass(kw_only=True)
class ChatMessageResponseDTO(BaseDTO):
    id: str
    chat_id: str
    user_id: Optional[str]
    content: Optional[str]
    is_read: bool
    sender_name: str
    is_admin: bool
    is_edited: bool
    is_deleted: bool
    attachments: List[MediaAssetResponseDTO]

    @classmethod
    def from_model(cls, obj: "ChatMessage") -> "ChatMessageResponseDTO":
        is_admin = False
        sender_name = "System"
        if obj.user:
            is_admin = getattr(obj.user, 'is_admin', False)
            sender_name = obj.user.get_name() if hasattr(obj.user, 'get_name') else (obj.user.first_name + " " + obj.user.last_name if obj.user.first_name else obj.user.username)
        
        att_list = []
        if hasattr(obj, 'attachments') and obj.attachments:
            att_list = [MediaAssetResponseDTO.from_model(a) for a in obj.attachments if not getattr(a, 'is_deleted', False)]

        is_deleted = getattr(obj, 'is_deleted', False)
        return cls(
            id=str(obj.id),
            chat_id=str(obj.chat_id) if obj.chat_id else "",
            user_id=str(obj.user_id) if obj.user_id else None,
            content=None if is_deleted else obj.content,
            is_read=obj.is_read,
            sender_name=sender_name,
            is_admin=is_admin,
            is_edited=getattr(obj, 'is_edited', False),
            is_deleted=is_deleted,
            attachments=att_list if not is_deleted else [],
            created_at=obj.created_at,
            updated_at=obj.updated_at
        )

@dataclass(kw_only=True)
class ChatResponseDTO(BaseDTO):
    id: str
    user_id: str
    user_name: str
    admin_id: Optional[str]
    admin_name: Optional[str]
    subject: Optional[str]
    order_id: Optional[str]
    order_number: Optional[str]
    status: str
    messages: Optional[list[ChatMessageResponseDTO]] = None
    unread_count: int = 0

    @classmethod
    def from_model(cls, obj: "Chat", current_user_id: Optional[str] = None, include_messages: bool = True, unread_count: Optional[int] = None) -> "ChatResponseDTO":
        user_name = (obj.user.get_name() if hasattr(obj.user, 'get_name') else (obj.user.first_name + " " + obj.user.last_name if obj.user.first_name else obj.user.username)) if obj.user else "Client"
        admin_name = ""
        if obj.admin:
            admin_name = obj.admin.get_name() if hasattr(obj.admin, 'get_name') else (obj.admin.first_name + " " + obj.admin.last_name if obj.admin.first_name else obj.admin.username)
        
        if unread_count is None:
            unread_count = 0
            for m in obj.messages:
                if not m.is_read:
                    if current_user_id and str(m.user_id) != str(current_user_id):
                        unread_count += 1
                    elif not current_user_id:
                        unread_count += 1

        messages_dto = None
        if include_messages:
            messages_dto = [ChatMessageResponseDTO.from_model(m) for m in obj.messages]

        return cls(
            id=str(obj.id),
            user_id=str(obj.user_id),
            user_name=user_name,
            admin_id=str(obj.admin_id) if obj.admin_id else None,
            admin_name=admin_name if obj.admin_id else None,
            subject=obj.subject,
            order_id=str(obj.order_id) if obj.order_id else None,
            order_number=obj.order.order_number if obj.order else None,
            status=obj.status.value if hasattr(obj.status, 'value') else str(obj.status),
            messages=messages_dto,
            unread_count=unread_count,
            created_at=obj.created_at,
            updated_at=obj.updated_at
        )

@dataclass
class ChatMessagePageDTO:
    messages: List[ChatMessageResponseDTO]
    has_more: bool
    next_cursor: Optional[str]
