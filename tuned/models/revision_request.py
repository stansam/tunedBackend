from tuned.extensions import db
from tuned.models.base import BaseModel
from datetime import datetime, timezone
from tuned.models.enums import RevisionRequestStatus, Priority
from sqlalchemy.orm import validates, Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tuned.models.order import Order
    from tuned.models.user import User
    from tuned.models.order_delivery import OrderDelivery

class OrderRevisionRequest(BaseModel):
    __tablename__ = 'order_revision_requests'

    # Foreign Keys
    order_id: Mapped[str] = mapped_column(db.String(36), db.ForeignKey('order.id', ondelete='CASCADE'), nullable=False, index=True)
    delivery_id: Mapped[str] = mapped_column(db.String(36), db.ForeignKey('order_delivery.id', ondelete='CASCADE'), nullable=False)
    requested_by: Mapped[str] = mapped_column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    reviewed_by: Mapped[Optional[str]] = mapped_column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    
    revision_notes: Mapped[str] = mapped_column(db.Text, nullable=False)
    internal_notes: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    
    status: Mapped[RevisionRequestStatus] = mapped_column(db.Enum(RevisionRequestStatus), default=RevisionRequestStatus.PENDING, nullable=False, index=True)
    priority: Mapped[Priority] = mapped_column(db.Enum(Priority), default=Priority.NORMAL, nullable=False)
    

    requested_at: Mapped[datetime] = mapped_column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    
    revision_count: Mapped[int] = mapped_column(db.Integer, default=1, nullable=False)
    estimated_completion: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    
    order: Mapped["Order"] = relationship('Order', back_populates='revision_requests')
    delivery: Mapped["OrderDelivery"] = relationship('OrderDelivery', back_populates='revision_requests')
    requester: Mapped["User"] = relationship('User', foreign_keys=[requested_by])
    reviewer: Mapped[Optional["User"]] = relationship('User', foreign_keys=[reviewed_by])
    
    __table_args__ = (
        db.Index('ix_revision_request_order_status', 'order_id', 'status'),
        db.Index('ix_revision_request_created', 'requested_at'),
    )
    
    @validates('status')
    def validate_status_transition(self, new_status: RevisionRequestStatus) -> RevisionRequestStatus: #key: str, 
        if not self.id or not hasattr(self, '_sa_instance_state') or self._sa_instance_state.key is None:
            return new_status
        
        current_status = self.status
        if current_status == new_status:
            return new_status
        
        valid_transitions = {
            RevisionRequestStatus.PENDING: [
                RevisionRequestStatus.IN_PROGRESS,
                RevisionRequestStatus.REJECTED,
                RevisionRequestStatus.CANCELLED
            ],
            RevisionRequestStatus.IN_PROGRESS: [
                RevisionRequestStatus.COMPLETED,
                RevisionRequestStatus.CANCELLED
            ],
            RevisionRequestStatus.COMPLETED: [],
            RevisionRequestStatus.REJECTED: [],
            RevisionRequestStatus.CANCELLED: [],
        }
        
        allowed = valid_transitions.get(current_status, [])
        if new_status not in allowed:
            raise ValueError(f'Invalid revision request status transition from {current_status.value} to {new_status.value}')
        
        return new_status
    
    @property
    def is_active(self) -> bool:
        return self.status in [
            RevisionRequestStatus.PENDING,
            RevisionRequestStatus.IN_PROGRESS
        ]
    
    @property
    def status_color(self) -> str:
        colors = {
            RevisionRequestStatus.PENDING: 'warning',
            RevisionRequestStatus.IN_PROGRESS: 'primary',
            RevisionRequestStatus.COMPLETED: 'success',
            RevisionRequestStatus.REJECTED: 'danger',
            RevisionRequestStatus.CANCELLED: 'secondary',
        }
        return colors.get(self.status, 'secondary')
    
    def to_dict(self, include_internal: bool = False) -> dict[str, Any]:
        data = {
            'id': self.id,
            'order_id': self.order_id,
            'order_number': self.order.order_number if self.order else None,
            'delivery_id': self.delivery_id,
            'revision_notes': self.revision_notes,
            'status': self.status.value,
            'priority': self.priority.value,
            'revision_count': self.revision_count,
            'requested_at': self.requested_at.isoformat() if self.requested_at else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'estimated_completion': self.estimated_completion.isoformat() if self.estimated_completion else None,
            'requester': {
                'id': self.requester.id,
                'name': self.requester.get_name(),
                'email': self.requester.email
            } if self.requester else None,
            'is_active': self.is_active,
        }
        
        if include_internal:
            data['internal_notes'] = self.internal_notes
            data['reviewer'] = {
                'id': self.reviewer.id,
                'name': self.reviewer.get_name(),
                'email': self.reviewer.email
            } if self.reviewer else None
        
        return data
    
    def __repr__(self) -> str:
        return f'<OrderRevisionRequest {self.id} for Order {self.order_id}>'
