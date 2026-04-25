from datetime import datetime, timezone
from flask import url_for 
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from tuned.extensions import db
from tuned.models.base import BaseModel
from tuned.models.communication import ChatMessage, Chat
from tuned.models.enums import GenderEnum
import secrets
import string

class User(UserMixin, BaseModel):
    __tablename__ = 'users'

    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    failed_login_attempts = db.Column(db.Integer, default=0)
    last_failed_login = db.Column(db.DateTime)

    email_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(128), nullable=True, index=True)
    email_verification_token_expires_at = db.Column(db.DateTime(timezone=True), nullable=True)
    
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.Enum(GenderEnum), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    profile_pic = db.Column(db.String(120), nullable=True, default='default.png')

    is_admin = db.Column(db.Boolean, default=False, server_default='false')

    referral_code = db.Column(db.String(10), unique=True) 
    reward_points = db.Column(db.Integer, default=0)

    braintree_customer_id = db.Column(db.String(50))

    last_login_at = db.Column(db.DateTime, nullable=True)
    
    language = db.Column(db.String(10), default='en', nullable=True)  # ISO 639-1
    timezone = db.Column(db.String(50), default='UTC', nullable=True)  # IANA timezone
    
    # Relationships
    orders = db.relationship('Order', foreign_keys='Order.client_id', back_populates='client', lazy=True)
    referrals = db.relationship('Referral', foreign_keys='Referral.referrer_id', backref='referrer', lazy=True)
    referred_by = db.relationship('Referral', foreign_keys='Referral.referred_id', backref='referred', lazy=True)
    notifications = db.relationship('Notification', foreign_keys="Notification.user_id", backref='user', lazy=True)
    testimonials = db.relationship('Testimonial', foreign_keys="Testimonial.user_id", backref='author', lazy=True, cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()

    def generate_referral_code(self):
        return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(10))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_name(self):
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
        if self.profile_pic and self.profile_pic != 'default.png':
            return url_for('static', filename=f'client/assets/profile_pics/{self.profile_pic}', _external=True)
            
        if self.gender == GenderEnum.FEMALE:
            return url_for('static', filename='ladyDefault.png', _external=True)
        return url_for('static', filename='manDefault.png', _external=True)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
