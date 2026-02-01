"""
Order Revision Request model.

Tracks client requests for revisions after order delivery.
"""
from tuned.extensions import db
from datetime import datetime, timezone
from tuned.models.enums import RevisionRequestStatus, Priority
from sqlalchemy.orm import validates


class OrderRevisionRequest(db.Model):
    """
    Track client revision requests for delivered orders.
    
    This model maintains a complete audit trail of revision requests,
    including who requested it, when, what was requested, and the outcome.
    """
    
    __tablename__ = 'order_revision_requests'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Keys
    order_id = db.Column(
        db.Integer,
        db.ForeignKey('order.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    delivery_id = db.Column(
        db.Integer,
        db.ForeignKey('order_deliveries.id', ondelete='CASCADE'),
        nullable=False
    )
    requested_by = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=False
    )
    reviewed_by = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=True
    )
    
    # Request Details
    revision_notes = db.Column(db.Text, nullable=False)  # Client's revision requirements
    internal_notes = db.Column(db.Text, nullable=True)   # Admin notes (not shown to client)
    
    # Status & Tracking
    status = db.Column(
        db.Enum(RevisionRequestStatus),
        default=RevisionRequestStatus.PENDING,
        nullable=False,
        index=True
    )
    priority = db.Column(
        db.Enum(Priority),
        default=Priority.NORMAL,
        nullable=False
    )
    
    # Timestamps
    requested_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    reviewed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    resolved_at = db.Column(db.DateTime(timezone=True), nullable=True)
    
    # Metadata
    revision_count = db.Column(db.Integer, default=1, nullable=False)  # 1st, 2nd, 3rd revision, etc.
    estimated_completion = db.Column(db.DateTime(timezone=True), nullable=True)
    
    # Relationships
    order = db.relationship(
        'Order',
        backref=db.backref('revision_requests', lazy='dynamic', cascade='all, delete-orphan')
    )
    delivery = db.relationship(
        'OrderDelivery',
        backref=db.backref('revision_requests', lazy='dynamic')
    )
    requester = db.relationship('User', foreign_keys=[requested_by])
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])
    
    # Indexes for performance
    __table_args__ = (
        db.Index('ix_revision_request_order_status', 'order_id', 'status'),
        db.Index('ix_revision_request_created', 'requested_at'),
    )
    
    @validates('status')
    def validate_status_transition(self, key, new_status):
        """
        Validate revision request status transitions.
        
        Valid transitions:
        - PENDING → IN_PROGRESS, REJECTED, CANCELLED
        - IN_PROGRESS → COMPLETED, CANCELLED
        - COMPLETED, REJECTED, CANCELLED → [terminal states, no transitions]
        """
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
            raise ValueError(
                f'Invalid revision request status transition from {current_status.value} to {new_status.value}'
            )
        
        return new_status
    
    @property
    def is_active(self):
        """Check if revision request is still active (not in terminal state)."""
        return self.status in [
            RevisionRequestStatus.PENDING,
            RevisionRequestStatus.IN_PROGRESS
        ]
    
    @property
    def status_color(self):
        """Get color for status display in UI."""
        colors = {
            RevisionRequestStatus.PENDING: 'warning',
            RevisionRequestStatus.IN_PROGRESS: 'primary',
            RevisionRequestStatus.COMPLETED: 'success',
            RevisionRequestStatus.REJECTED: 'danger',
            RevisionRequestStatus.CANCELLED: 'secondary',
        }
        return colors.get(self.status, 'secondary')
    
    def to_dict(self, include_internal=False):
        """
        Convert revision request to dictionary.
        
        Args:
            include_internal: If True, include internal_notes (admin only)
        """
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
    
    def __repr__(self):
        return f'<OrderRevisionRequest {self.id} for Order {self.order_id}>'
