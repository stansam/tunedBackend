import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import func
from tuned.extensions import db
from tuned.models.base import BaseModel
if TYPE_CHECKING:
    from tuned.models.user import User

class UserPolicyAcceptance(BaseModel):
    __tablename__ = 'user_policy_acceptances'

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        db.ForeignKey('users.id', ondelete='CASCADE', name='fk_user_policy_acceptances_user_id'),
        nullable=False,
        index=True
    )
    terms_version: Mapped[str] = mapped_column(db.String(20), nullable=False)
    privacy_version: Mapped[str] = mapped_column(db.String(20), nullable=False)
    accepted_at: Mapped[datetime] = mapped_column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(db.String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="policy_acceptances")

    def __init__(self, **kwargs) -> None:
        super(UserPolicyAcceptance, self).__init__(**kwargs)
