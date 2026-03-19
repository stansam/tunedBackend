from tuned.extensions import db
from tuned.models.base import BaseModel
from datetime import datetime, timezone
from tuned.models.enums import NotificationType, ChatStatus, NewsletterFrequency, NewsletterFormat
from sqlalchemy.dialects.postgresql import ARRAY

class Notification(BaseModel):
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.Enum(NotificationType), default=NotificationType.INFO, nullable=False)
    link = db.Column(db.String(255),    nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    
    # Table arguments for indexes
    __table_args__ = (
        db.Index('ix_notification_user_read_created', 'user_id', 'is_read', 'created_at'),
    )

    def mark_as_read(self):
        self.is_read = True
        db.session.commit()
    
    def to_dict(self):
        return {
            'id':         self.id,
            'title':      self.title,
            'message':    self.message,
            'type':       self.type.value,
            'link':       self.link,
            'is_read':    self.is_read,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<Notification {self.title}>'

class NewsletterSubscriber(BaseModel):
    __tablename__ = 'newsletter_subscriber'
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    subscribed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    frequency = db.Column(
        db.Enum(NewsletterFrequency),
        default=NewsletterFrequency.WEEKLY,
        nullable=False
    )
    topics = db.Column(db.JSON, nullable=True)
    format = db.Column(
        db.Enum(NewsletterFormat),
        default=NewsletterFormat.HTML,
        nullable=False
    )
    
    def __repr__(self):
        return f'<NewsletterSubscriber {self.email}>'
    
class Chat(BaseModel):
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    admin_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    subject = db.Column(db.String(255))
    order_id = db.Column(db.String(36), db.ForeignKey('order.id'), nullable=True)
    status = db.Column(db.Enum(ChatStatus), default=ChatStatus.ACTIVE, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    messages = db.relationship('ChatMessage', backref='chat', lazy="dynamic", cascade="all, delete-orphan")
    user = db.relationship('User', foreign_keys=[user_id], backref='user_chats')
    admin = db.relationship('User', foreign_keys=[admin_id], backref='admin_chats')
    order = db.relationship('Order', backref='chats')
    
    def __repr__(self):
        return f'<Chat {self.id}>'
    
class ChatMessage(BaseModel):
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    chat_id = db.Column(db.String(36), db.ForeignKey('chat.id'))
    content = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='chat_messages')
    
    # Table arguments for indexes
    __table_args__ = (
        db.Index('ix_chat_message_chat_created', 'chat_id', 'created_at'),
    )
    
    def __repr__(self):
        return f'<ChatMessage {self.id} by User {self.user_id}>'