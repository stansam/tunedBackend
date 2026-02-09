"""
Database model enumerations for type safety and validation.

This module contains all enum types used across database models.
"""
import enum

class GenderEnum(enum.Enum):
    male = "male"
    female = "female"

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


class RevisionRequestStatus(enum.Enum):
    """Revision request status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ExtensionRequestStatus(enum.Enum):
    """Deadline extension request status enumeration"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class Priority(enum.Enum):
    """Priority levels for requests and tasks"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


# ============================================================================
# USER PREFERENCE ENUMS
# ============================================================================

class EmailFrequency(enum.Enum):
    """Email notification frequency preferences"""
    INSTANT = "instant"
    DAILY = "daily"
    WEEKLY = "weekly"


class ProfileVisibility(enum.Enum):
    """User profile visibility settings"""
    PUBLIC = "public"
    PRIVATE = "private"
    FRIENDS_ONLY = "friends_only"


class DateFormat(enum.Enum):
    """Date format preferences"""
    MM_DD_YYYY = "MM/DD/YYYY"
    DD_MM_YYYY = "DD/MM/YYYY"
    YYYY_MM_DD = "YYYY-MM-DD"


class TimeFormat(enum.Enum):
    """Time format preferences"""
    TWELVE_HOUR = "12h"
    TWENTY_FOUR_HOUR = "24h"


class NumberFormat(enum.Enum):
    """Number format preferences"""
    COMMA_DOT = "1,234.56"
    DOT_COMMA = "1.234,56"
    SPACE_COMMA = "1 234,56"


class WeekStart(enum.Enum):
    """First day of week preference"""
    SUNDAY = "sunday"
    MONDAY = "monday"


class NewsletterFrequency(enum.Enum):
    """Newsletter subscription frequency"""
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"


class NewsletterFormat(enum.Enum):
    """Newsletter format preference"""
    HTML = "html"
    TEXT = "text"


class InvoiceDeliveryMethod(enum.Enum):
    """Invoice delivery preference"""
    EMAIL = "email"
    DOWNLOAD_ONLY = "download_only"


class RuleType(enum.Enum):
    """Preference rule type for conditional preferences"""
    NOTIFICATION = "notification"
    EMAIL = "email"


class ExperimentStatus(enum.Enum):
    """A/B test experiment status"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class SuggestionStatus(enum.Enum):
    """ML personalization suggestion status"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DISMISSED = "dismissed"

