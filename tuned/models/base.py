import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from typing import Optional
from tuned.extensions import db
from sqlalchemy import func
class BaseModel(db.Model):  # type: ignore[name-defined, misc]
    __abstract__ = True
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(db.DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, index=True)
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False, index=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True, index=True)
    deleted_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=True)