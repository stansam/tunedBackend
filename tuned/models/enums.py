"""
Database model enumerations for type safety and validation.

This module contains all enum types used across database models.
"""
import enum


class OrderStatus(enum.Enum):
    """Order status enumeration"""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED_PENDING_REVIEW = "completed pending review"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELED = "canceled"
    REVISION = "revision"


class PaymentStatus(enum.Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethod(enum.Enum):
    """Payment method enumeration"""
    CREDIT_CARD = "credit_card"
    PAYPAL = "paypal"
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"


class TransactionType(enum.Enum):
    """Transaction type enumeration"""
    PAYMENT = "payment"
    REFUND = "refund"
    CHARGEBACK = "chargeback"


class RefundStatus(enum.Enum):
    """Refund status enumeration"""
    PENDING = "pending"
    PROCESSED = "processed"
    DENIED = "denied"


class NotificationType(enum.Enum):
    """Notification type enumeration"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class ChatStatus(enum.Enum):
    """Chat status enumeration"""
    ACTIVE = "active"
    CLOSED = "closed"


class FileType(enum.Enum):
    """Order delivery file type enumeration"""
    DELIVERY = "delivery"
    PLAGIARISM_REPORT = "plagiarism_report"
    SUPPLEMENTARY = "supplementary"


class DeliveryStatus(enum.Enum):
    """Order delivery status enumeration"""
    DELIVERED = "delivered"
    REVISED = "revised"
    REDELIVERED = "redelivered"


class SupportTicketStatus(enum.Enum):
    """Support ticket status enumeration"""
    OPEN = "open"
    CLOSED = "closed"
    IN_PROGRESS = "in_progress"


class ReferralStatus(enum.Enum):
    """Referral status enumeration"""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"


class DiscountType(enum.Enum):
    """Discount type enumeration"""
    PERCENTAGE = "percentage"
    FIXED = "fixed"


class Currency(enum.Enum):
    """Currency enumeration (ISO 4217)"""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CAD = "CAD"
    AUD = "AUD"
    # Add more currencies as needed
