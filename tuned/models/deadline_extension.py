"""
Order Deadline Extension Request model.

Tracks admin requests for deadline extensions on active orders.
When the admin needs more time to complete work, they request an extension from the client.
"""
from tuned.extensions import db
from datetime import datetime, timezone, timedelta
from tuned.models.enums import ExtensionRequestStatus, Priority
from sqlalchemy.orm import validates


class OrderDeadlineExtensionRequest(db.Model):
    """
    Track admin deadline extension requests for active orders.
    
    When the admin/service provider needs more time to complete an order,
    they submit an extension request which the client can approve or reject.
    This maintains a complete audit trail of extension requests and decisions.
    """
    
    __tablename__ = 'order_deadline_extension_requests'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Keys
    order_id = db.Column(
        db.Integer,
        db.ForeignKey('order.id', ondelete='CASCADE'),
        nullable=False,
        index=True
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
    requested_hours = db.Column(db.Integer, nullable=False)  # Hours of extension requested by admin
    reason = db.Column(db.Text, nullable=False)  # Admin's reason for needing more time
    client_notes = db.Column(db.Text, nullable=True)  # Client notes when approving/rejecting
    
    # Deadline Information
    original_due_date = db.Column(db.DateTime(timezone=True), nullable=False)
    new_due_date = db.Column(db.DateTime(timezone=True), nullable=True)  # Set when approved by client
    
    # Status & Tracking
    status = db.Column(
        db.Enum(ExtensionRequestStatus),
        default=ExtensionRequestStatus.PENDING,
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
    
    # Metadata
    rejection_reason = db.Column(db.Text, nullable=True)  # Client's reason for rejection
    
    # Relationships
    order = db.relationship(
        'Order',
        backref=db.backref('deadline_extension_requests', lazy='dynamic', cascade='all, delete-orphan')
    )
    requester = db.relationship('User', foreign_keys=[requested_by])  # Admin who requested
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])  # Client who approved/rejected
    
    # Indexes for performance
    __table_args__ = (
        db.Index('ix_extension_request_order_status', 'order_id', 'status'),
        db.Index('ix_extension_request_created', 'requested_at'),
    )
    
    @validates('status')
    def validate_status_transition(self, key, new_status):
        """
        Validate deadline extension request status transitions.
        
        Valid transitions:
        - PENDING → APPROVED, REJECTED, CANCELLED
        - APPROVED, REJECTED, CANCELLED → [terminal states, no transitions]
        """
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
            raise ValueError(
                f'Invalid extension request status transition from {current_status.value} to {new_status.value}'
            )
        
        return new_status
    
    @property
    def is_pending(self):
        """Check if extension request is still pending."""
        return self.status == ExtensionRequestStatus.PENDING
    
    @property
    def status_color(self):
        """Get color for status display in UI."""
        colors = {
            ExtensionRequestStatus.PENDING: 'warning',
            ExtensionRequestStatus.APPROVED: 'success',
            ExtensionRequestStatus.REJECTED: 'danger',
            ExtensionRequestStatus.CANCELLED: 'secondary',
        }
        return colors.get(self.status, 'secondary')
    
    @property
    def hours_difference(self):
        """Calculate actual hours granted (for approved requests)."""
        if self.new_due_date and self.original_due_date:
            delta = self.new_due_date - self.original_due_date
            return int(delta.total_seconds() / 3600)
        return None
    
    def to_dict(self, include_client_notes=False):
        """
        Convert deadline extension request to dictionary.
        
        Args:
            include_client_notes: If True, include client_notes (for client/admin)
        """
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
    
    def __repr__(self):
        return f'<OrderDeadlineExtensionRequest {self.id} for Order {self.order_id}>'
