from datetime import datetime, timezone
from flask import url_for 
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from tuned.extensions import db
from tuned.models.communication import ChatMessage, Chat
import enum

class GenderEnum(enum.Enum):
    male = "male"
    female = "female"

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    failed_login_attempts = db.Column(db.Integer, default=0)
    last_failed_login = db.Column(db.DateTime)

    email_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(100))

    password_reset_token = db.Column(db.String(100), nullable=True)
    password_reset_expires = db.Column(db.DateTime, nullable=True)
    
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    gender = db.Column(db.Enum(GenderEnum), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    profile_pic = db.Column(db.String(120), nullable=True, default='default.png')

    is_admin = db.Column(db.Boolean, default=False, server_default='false')

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    referral_code = db.Column(db.String(10), unique=True) 
    reward_points = db.Column(db.Integer, default=0)

    braintree_customer_id = db.Column(db.String(50))

    # Soft delete and activity tracking
    is_active = db.Column(db.Boolean, default=True, server_default='true')
    deleted_at = db.Column(db.DateTime, nullable=True)
    last_login_at = db.Column(db.DateTime, nullable=True)

    # Table arguments for indexes
    __table_args__ = (
        db.Index('ix_user_email_verification_token', 'email_verification_token'),
        db.Index('ix_user_password_reset_token', 'password_reset_token'),
    )

    # Relationships
    orders = db.relationship('Order', foreign_keys='Order.client_id', backref='client', lazy=True)
    referrals = db.relationship('Referral', foreign_keys='Referral.referrer_id', backref='referrer', lazy=True)
    referred_by = db.relationship('Referral', foreign_keys='Referral.referred_id', backref='referred', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)
    testimonials = db.relationship('Testimonial', backref='author', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set the password hash from the provided password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches the stored hash."""
        return check_password_hash(self.password_hash, password)

    def get_name(self):
        """Return full name if available, otherwise username."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def get_unread_notification_count(self):
        return self.notifications.filter_by(is_read=False).count()
    
    def get_unread_message_count(self):
        from sqlalchemy import and_, or_
        return db.session.query(ChatMessage).join(Chat).filter(
            and_(
                or_(Chat.user_id == self.id, Chat.admin_id == self.id),
                ChatMessage.user_id != self.id,
                ChatMessage.is_read == False
            )
        ).count()
    
    def get_profile_pic_url(self):
        filename = self.profile_pic if self.profile_pic and self.profile_pic != 'default.png' else 'default.png'
    
        if self.is_admin:
            return url_for('admin.static', filename=f'assets/profile_pics/{filename}')
        return url_for('client.static', filename=f'client/assets/profile_pics/{filename}')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
