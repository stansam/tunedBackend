from tuned.extensions import db
from tuned.models.base import BaseModel
from datetime import datetime, timezone
from tuned.models.enums import ExtensionRequestStatus, Priority
from sqlalchemy.orm import validates, Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tuned.models.order import Order
    from tuned.models.user import User

class OrderDeadlineExtensionRequest(BaseModel):    
    __tablename__ = 'order_deadline_extension_requests'
    
    order_id: Mapped[str] = mapped_column(db.String(36), db.ForeignKey('order.id', ondelete='CASCADE'), nullable=False, index=True)
    requested_by: Mapped[str] = mapped_column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    reviewed_by: Mapped[Optional[str]] = mapped_column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    
    requested_hours: Mapped[int] = mapped_column(db.Integer, nullable=False)  # Hours of extension requested by admin
    reason: Mapped[str] = mapped_column(db.Text, nullable=False)  # Admin's reason for needing more time
    client_notes: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)  # Client notes when approving/rejecting
    
    original_due_date: Mapped[datetime] = mapped_column(db.DateTime(timezone=True), nullable=False)
    new_due_date: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)  # Set when approved by client

    status: Mapped[ExtensionRequestStatus] = mapped_column(db.Enum(ExtensionRequestStatus), default=ExtensionRequestStatus.PENDING, nullable=False, index=True)
    priority: Mapped[Priority] = mapped_column(db.Enum(Priority), default=Priority.NORMAL, nullable=False)

    requested_at: Mapped[datetime] = mapped_column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)  
    
    order: Mapped["Order"] = relationship('Order', back_populates='deadline_extension_requests')
    requester: Mapped["User"] = relationship('User', foreign_keys=[requested_by])
    reviewer: Mapped[Optional["User"]] = relationship('User', foreign_keys=[reviewed_by])
    
    __table_args__ = (
        db.Index('ix_extension_request_order_status', 'order_id', 'status'),
        db.Index('ix_extension_request_created', 'requested_at'),
    )
    
    @validates('status')
    def validate_status_transition(self, key: str, new_status: ExtensionRequestStatus) -> ExtensionRequestStatus:
        if not self.id or not hasattr(self, '_sa_instance_state') or self._sa_instance_state.key is None:
            return new_status
        
        current_status = self.status
        if current_status == new_status:
            return new_status
        
        valid_transitions = {
            ExtensionRequestStatus.PENDING: [
                ExtensionRequestStatus.APPROVED,
                ExtensionRequestStatus.REJECTED,
                ExtensionRequestStatus.CANCELLED
            ],
            ExtensionRequestStatus.APPROVED: [],
            ExtensionRequestStatus.REJECTED: [],
            ExtensionRequestStatus.CANCELLED: [],
        }
        
        allowed = valid_transitions.get(current_status, [])
        if new_status not in allowed:
            raise ValueError(f'Invalid extension request status transition from {current_status.value} to {new_status.value}')
        
        return new_status
    
    @property
    def is_pending(self) -> bool:
        return self.status == ExtensionRequestStatus.PENDING
    
    @property
    def status_color(self) -> str:
        colors = {
            ExtensionRequestStatus.PENDING: 'warning',
            ExtensionRequestStatus.APPROVED: 'success',
            ExtensionRequestStatus.REJECTED: 'danger',
            ExtensionRequestStatus.CANCELLED: 'secondary',
        }
        return colors.get(self.status, 'secondary')
    
    @property
    def hours_difference(self) -> Optional[int]:
        if self.new_due_date and self.original_due_date:
            delta = self.new_due_date - self.original_due_date
            return int(delta.total_seconds() / 3600)
        return None
    
    def to_dict(self, include_client_notes: bool = False) -> dict[str, Any]:
        data = {
            'id': self.id,
            'order_id': self.order_id,
            'order_number': self.order.order_number if self.order else None,
            'requested_hours': self.requested_hours,
            'reason': self.reason,
            'status': self.status.value,
            'priority': self.priority.value,
            'original_due_date': self.original_due_date.isoformat() if self.original_due_date else None,
            'new_due_date': self.new_due_date.isoformat() if self.new_due_date else None,
            'requested_at': self.requested_at.isoformat() if self.requested_at else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'requester': {
                'id': self.requester.id,
                'name': self.requester.get_name(),
                'email': self.requester.email
            } if self.requester else None,
            'is_pending': self.is_pending,
            'hours_granted': self.hours_difference,
        }
        
        if self.status == ExtensionRequestStatus.REJECTED:
            data['rejection_reason'] = self.rejection_reason
        
        if include_client_notes:
            data['client_notes'] = self.client_notes
            data['reviewer'] = {
                'id': self.reviewer.id,
                'name': self.reviewer.get_name(),
                'email': self.reviewer.email
            } if self.reviewer else None
        
        return data
    
    def __repr__(self) -> str:
        return f'<OrderDeadlineExtensionRequest {self.id} for Order {self.order_id}>'
