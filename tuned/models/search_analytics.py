import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from typing import Optional, Any
from tuned.extensions import db
from tuned.models.base import BaseModel

class SearchSession(BaseModel):
    __tablename__ = 'search_session'
    
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    session_key: Mapped[str] = mapped_column(db.String(100), unique=True, nullable=False, index=True)
    ip_address: Mapped[Optional[str]] = mapped_column(db.String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)

    def __init__(self, **kwargs: Any) -> None:
        super(SearchSession, self).__init__(**kwargs)

class SearchEvent(BaseModel):
    __tablename__ = 'search_event'
    
    query_text: Mapped[str] = mapped_column(db.String(200), nullable=False, index=True)
    search_type: Mapped[str] = mapped_column(db.String(50), nullable=False, default='all')
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), db.ForeignKey('search_session.id', ondelete='SET NULL'), nullable=True, index=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    result_count: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    device_type: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(db.String(45), nullable=True)
    source: Mapped[str] = mapped_column(db.String(50), default='hero', nullable=False)

    clicks: Mapped[list["SearchClick"]] = relationship('SearchClick', back_populates='event', cascade='all, delete-orphan')

    def __init__(self, **kwargs: Any) -> None:
        super(SearchEvent, self).__init__(**kwargs)

class SearchClick(BaseModel):
    __tablename__ = 'search_click'
    
    search_event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), db.ForeignKey('search_event.id', ondelete='CASCADE'), nullable=False, index=True)
    clicked_entity_type: Mapped[str] = mapped_column(db.String(50), nullable=False)
    clicked_entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    position: Mapped[int] = mapped_column(db.Integer, nullable=False)

    event: Mapped[SearchEvent] = relationship(SearchEvent, back_populates='clicks')

    def __init__(self, **kwargs: Any) -> None:
        super(SearchClick, self).__init__(**kwargs)

class PopularSearch(BaseModel):
    __tablename__ = 'popular_search'
    
    query_text: Mapped[str] = mapped_column(db.String(200), unique=True, nullable=False, index=True)
    search_count: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    last_searched_at: Mapped[datetime] = mapped_column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    def __init__(self, **kwargs: Any) -> None:
        super(PopularSearch, self).__init__(**kwargs)
