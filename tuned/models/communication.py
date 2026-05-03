from tuned.extensions import db
from tuned.models.base import BaseModel
from datetime import datetime, timezone
from tuned.models.enums import NotificationType, ChatStatus, NewsletterFrequency, NewsletterFormat
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional, Any

if TYPE_CHECKING:
    from tuned.models.user import User
    from tuned.models.order import Order

class Notification(BaseModel):
    __tablename__ = 'notification'
    user_id: Mapped[str] = mapped_column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    title: Mapped[str] = mapped_column(db.String(100), nullable=False)
    message: Mapped[str] = mapped_column(db.Text, nullable=False)
    type: Mapped[NotificationType] = mapped_column(db.Enum(NotificationType), default=NotificationType.INFO, nullable=False)
    link: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    is_read: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    
    __table_args__ = (
        db.Index('ix_notification_user_read_created', 'user_id', 'is_read', 'created_at'),
    )

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="notifications")

    def mark_as_read(self) -> None:
        self.is_read = True
        db.session.commit()
    
    def to_dict(self) -> dict[str, Any]:
        return {
            'id':         self.id,
            'title':      self.title,
            'message':    self.message,
            'type':       self.type.value,
            'link':       self.link,
            'is_read':    self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self) -> str:
        return f'<Notification {self.title}>'

class NewsletterSubscriber(BaseModel):
    __tablename__ = 'newsletter_subscriber'
    email: Mapped[str] = mapped_column(db.String(120), unique=True, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(db.String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    subscribed_at: Mapped[datetime] = mapped_column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    frequency: Mapped[NewsletterFrequency] = mapped_column(
        db.Enum(NewsletterFrequency),
        default=NewsletterFrequency.WEEKLY,
        nullable=False
    )
    topics: Mapped[Optional[dict[str, Any]]] = mapped_column(db.JSON, nullable=True)
    format: Mapped[NewsletterFormat] = mapped_column(
        db.Enum(NewsletterFormat),
        default=NewsletterFormat.HTML,
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f'<NewsletterSubscriber {self.email}>'
    
class Chat(BaseModel):
    __tablename__ = 'chat'
    user_id: Mapped[str] = mapped_column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    admin_id: Mapped[Optional[str]] = mapped_column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    subject: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    order_id: Mapped[Optional[str]] = mapped_column(db.String(36), db.ForeignKey('order.id'), nullable=True)
    status: Mapped[ChatStatus] = mapped_column(db.Enum(ChatStatus), default=ChatStatus.ACTIVE, nullable=False)
    
    # Relationships
    messages: Mapped[list["ChatMessage"]] = relationship('ChatMessage', back_populates='chat', lazy="dynamic", cascade="all, delete-orphan")
    user: Mapped["User"] = relationship('User', foreign_keys=[user_id], back_populates='user_chats')
    admin: Mapped[Optional["User"]] = relationship('User', foreign_keys=[admin_id], back_populates='admin_chats')
    order: Mapped[Optional["Order"]] = relationship('Order', back_populates='chats')
    
    def __repr__(self) -> str:
        return f'<Chat {self.id}>'
    
class ChatMessage(BaseModel):
    __tablename__ = 'chat_message'
    user_id: Mapped[Optional[str]] = mapped_column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    chat_id: Mapped[Optional[str]] = mapped_column(db.String(36), db.ForeignKey('chat.id'), nullable=True)
    content: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    is_read: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    
    # Relationships
    user: Mapped[Optional["User"]] = relationship('User', foreign_keys=[user_id], back_populates='chat_messages')
    chat: Mapped[Optional["Chat"]] = relationship('Chat', foreign_keys=[chat_id], back_populates='messages')
    
    __table_args__ = (
        db.Index('ix_chat_message_chat_created', 'chat_id', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f'<ChatMessage {self.id} by User {self.user_id}>'