import enum

class GenderEnum(enum.Enum):
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"

class OrderStatus(enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED_PENDING_REVIEW = "completed pending review"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELED = "canceled"
    REVISION = "revision"


class PaymentStatus(enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethod(enum.Enum):
    CREDIT_CARD = "credit_card"
    PAYPAL = "paypal"
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"


class TransactionType(enum.Enum):
    PAYMENT = "payment"
    REFUND = "refund"
    CHARGEBACK = "chargeback"


class RefundStatus(enum.Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    DENIED = "denied"


class NotificationType(enum.Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class ChatStatus(enum.Enum):
    ACTIVE = "active"
    CLOSED = "closed"


class FileType(enum.Enum):
    DELIVERY = "delivery"
    PLAGIARISM_REPORT = "plagiarism_report"
    SUPPLEMENTARY = "supplementary"


class DeliveryStatus(enum.Enum):
    DELIVERED = "delivered"
    REVISED = "revised"
    REDELIVERED = "redelivered"


class SupportTicketStatus(enum.Enum):
    OPEN = "open"
    CLOSED = "closed"
    IN_PROGRESS = "in_progress"


class ReferralStatus(enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"


class DiscountType(enum.Enum):
    PERCENTAGE = "percentage"
    FIXED = "fixed"


class Currency(enum.Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CAD = "CAD"
    AUD = "AUD"


class RevisionRequestStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ExtensionRequestStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class Priority(enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class EmailFrequency(enum.Enum):
    INSTANT = "instant"
    DAILY = "daily"
    WEEKLY = "weekly"


class ProfileVisibility(enum.Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    FRIENDS_ONLY = "friends_only"


class DateFormat(enum.Enum):
    MM_DD_YYYY = "MM/DD/YYYY"
    DD_MM_YYYY = "DD/MM/YYYY"
    YYYY_MM_DD = "YYYY-MM-DD"


class TimeFormat(enum.Enum):
    TWELVE_HOUR = "12h"
    TWENTY_FOUR_HOUR = "24h"


class NumberFormat(enum.Enum):
    COMMA_DOT = "1,234.56"
    DOT_COMMA = "1.234,56"
    SPACE_COMMA = "1 234,56"


class WeekStart(enum.Enum):
    SUNDAY = "sunday"
    MONDAY = "monday"


class NewsletterFrequency(enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"


class NewsletterFormat(enum.Enum):
    HTML = "html"
    TEXT = "text"


class InvoiceDeliveryMethod(enum.Enum):
    EMAIL = "email"
    DOWNLOAD_ONLY = "download_only"


class RuleType(enum.Enum):
    NOTIFICATION = "notification"
    EMAIL = "email"


class ExperimentStatus(enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class SuggestionStatus(enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DISMISSED = "dismissed"

class BlogReactionType(enum.Enum):
    LIKE = "like"
    DISLIKE = "dislike"

