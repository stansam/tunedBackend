from enum import Enum

class GenderEnum(str, Enum):
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"

class OrderStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED_PENDING_REVIEW = "completed pending review"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELED = "canceled"
    REVISION = "revision"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethod(str, Enum):
    CREDIT_CARD = "credit_card"
    PAYPAL = "paypal"
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"


class TransactionType(str, Enum):
    PAYMENT = "payment"
    REFUND = "refund"
    CHARGEBACK = "chargeback"


class RefundStatus(str, Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    DENIED = "denied"


class NotificationType(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class ChatStatus(str, Enum):
    ACTIVE = "active"
    CLOSED = "closed"


class FileType(str, Enum):
    DELIVERY = "delivery"
    PLAGIARISM_REPORT = "plagiarism_report"
    SUPPLEMENTARY = "supplementary"


class DeliveryStatus(str, Enum):
    DELIVERED = "delivered"
    REVISED = "revised"
    REDELIVERED = "redelivered"


class SupportTicketStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    IN_PROGRESS = "in_progress"


class ReferralStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"


class DiscountType(str, Enum):
    PERCENTAGE = "percentage"
    FIXED = "fixed"


class Currency(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CAD = "CAD"
    AUD = "AUD"


class RevisionRequestStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ExtensionRequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class Priority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class EmailFrequency(str, Enum):
    INSTANT = "instant"
    DAILY = "daily"
    WEEKLY = "weekly"


class ProfileVisibility(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    FRIENDS_ONLY = "friends_only"


class DateFormat(str, Enum):
    MM_DD_YYYY = "MM/DD/YYYY"
    DD_MM_YYYY = "DD/MM/YYYY"
    YYYY_MM_DD = "YYYY-MM-DD"


class TimeFormat(str, Enum):
    TWELVE_HOUR = "12h"
    TWENTY_FOUR_HOUR = "24h"


class NumberFormat(str, Enum):
    COMMA_DOT = "1,234.56"
    DOT_COMMA = "1.234,56"
    SPACE_COMMA = "1 234,56"


class WeekStart(str, Enum):
    SUNDAY = "sunday"
    MONDAY = "monday"


class NewsletterFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"


class NewsletterFormat(str, Enum):
    HTML = "html"
    TEXT = "text"


class InvoiceDeliveryMethod(str, Enum):
    EMAIL = "email"
    DOWNLOAD_ONLY = "download_only"


class RuleType(str, Enum):
    NOTIFICATION = "notification"
    EMAIL = "email"


class ExperimentStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class SuggestionStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DISMISSED = "dismissed"

class BlogReactionType(str, Enum):
    LIKE = "like"
    DISLIKE = "dislike"

class ActionableAlertType(str, Enum):
    EXTENSION_REQUEST = "EXTENSION_REQUEST"
    PENDING_REVIEW    = "PENDING_REVIEW"

