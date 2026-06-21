from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_
from tuned.models.communication import Chat, ChatMessage
from tuned.dtos.communication import CreateChatDTO
from tuned.repository.exceptions import DatabaseError, NotFound
from sqlalchemy.exc import SQLAlchemyError
from tuned.models.enums import ChatStatus
from typing import Optional, List

class ChatRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, chat_id: str) -> Optional[Chat]:
        try:
            stmt = select(Chat).where(Chat.id == chat_id)
            return self.session.scalar(stmt)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching chat: {str(e)}") from e

    def get_chat_for_user(self, chat_id: str, user_id: str, is_admin: bool = False) -> Optional[Chat]:
        try:
            if is_admin:
                stmt = select(Chat).where(Chat.id == chat_id)
            else:
                stmt = select(Chat).where(and_(Chat.id == chat_id, Chat.user_id == user_id))
            return self.session.scalar(stmt)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching chat: {str(e)}") from e

    def list_client_chats(self, user_id: str) -> List[Chat]:
        try:
            stmt = select(Chat).where(Chat.user_id == user_id).order_by(Chat.created_at.desc())
            return list(self.session.scalars(stmt).all())
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while listing client chats: {str(e)}") from e

    def list_all_chats_admin(self) -> List[Chat]:
        try:
            stmt = select(Chat).order_by(Chat.created_at.desc())
            return list(self.session.scalars(stmt).all())
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while listing all chats: {str(e)}") from e

    def create_chat(self, data: CreateChatDTO) -> Chat:
        try:
            chat = Chat(
                user_id=data.user_id,
                subject=data.subject,
                order_id=data.order_id,
                status=ChatStatus.ACTIVE
            )
            self.session.add(chat)
            self.session.flush()
            return chat
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while creating chat: {str(e)}") from e

    def create_message(self, chat_id: str, user_id: str, content: str) -> ChatMessage:
        try:
            msg = ChatMessage(
                chat_id=chat_id,
                user_id=user_id,
                content=content,
                is_read=False
            )
            self.session.add(msg)
            self.session.flush()
            return msg
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while creating message: {str(e)}") from e

    def mark_as_read(self, chat_id: str, user_id: str) -> List[ChatMessage]:
        try:
            stmt = select(ChatMessage).where(
                and_(
                    ChatMessage.chat_id == chat_id,
                    ChatMessage.user_id != user_id,
                    ChatMessage.is_read == False
                )
            )
            messages = list(self.session.scalars(stmt).all())
            for msg in messages:
                msg.is_read = True
            self.session.flush()
            return messages
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while marking messages as read: {str(e)}") from e

    def assign_admin(self, chat_id: str, admin_id: str) -> Chat:
        try:
            stmt = select(Chat).where(Chat.id == chat_id)
            chat = self.session.scalar(stmt)
            if not chat:
                raise NotFound("Chat not found")
            chat.admin_id = UUID(admin_id)
            self.session.flush()
            return chat
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while assigning admin: {str(e)}") from e

    def update_status(self, chat_id: str, status: ChatStatus) -> Chat:
        try:
            stmt = select(Chat).where(Chat.id == chat_id)
            chat = self.session.scalar(stmt)
            if not chat:
                raise NotFound("Chat not found")
            chat.status = status
            self.session.flush()
            return chat
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while updating status: {str(e)}") from e

    def save(self) -> None:
        try:
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f"Database error while saving: {str(e)}") from e
        
    def rollback(self) -> None:
        self.session.rollback()
