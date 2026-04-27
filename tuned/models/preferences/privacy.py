from tuned.extensions import db
from tuned.models.enums import ProfileVisibility
from tuned.models.base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tuned.models.user import User

class UserPrivacySettings(BaseModel):
    __tablename__ = 'user_privacy_settings'

    user_id: Mapped[str] = mapped_column(
        db.String(36),
        db.ForeignKey('users.id', ondelete='CASCADE'),
        unique=True,
        nullable=False,
        index=True
    )
    
    profile_visibility: Mapped[ProfileVisibility] = mapped_column(
        db.Enum(ProfileVisibility),
        default=ProfileVisibility.PRIVATE,
        nullable=False
    )
    show_email: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    show_phone: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    show_name: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    
    allow_messages: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    allow_comments: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    
    data_sharing: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    analytics_tracking: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    third_party_cookies: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    
    allow_search_engine_indexing: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    
    user: Mapped["User"] = relationship('User', foreign_keys=[user_id], back_populates='privacy_settings')
    
    def to_dict(self) -> dict[str, Any]:
        return {
            'profile_visibility': self.profile_visibility.value if self.profile_visibility else 'private',
            'show_email': self.show_email,
            'show_phone': self.show_phone,
            'show_name': self.show_name,
            'allow_messages': self.allow_messages,
            'allow_comments': self.allow_comments,
            'data_sharing': self.data_sharing,
            'analytics_tracking': self.analytics_tracking,
            'third_party_cookies': self.third_party_cookies,
            'allow_search_engine_indexing': self.allow_search_engine_indexing,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self) -> str:
        return f'<UserPrivacySettings user_id={self.user_id}>'
