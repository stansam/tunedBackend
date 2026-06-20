from tuned.repository.protocols.user import UserRepositoryProtocol
from tuned.repository.protocols.referral import ReferralRepositoryProtocol
from tuned.repository.protocols.blogs import BlogRepositoryProtocol
from tuned.repository.protocols.content import (
    AcademicLevelRepositoryProtocol, DeadlineRepositoryProtocol, FAQRepositoryProtocol,
    SampleRepositoryProtocol, ServiceCategoryRepositoryProtocol, ServiceRepositoryProtocol,
    TestimonialRepositoryProtocol
)
from tuned.repository.protocols.audit import (
    ActivityLogRepositoryProtocol, EmailLogRepositoryProtocol,
    OrderStatusHistoryRepositoryProtocol, PriceHistoryRepositoryProtocol
)
from tuned.repository.protocols.order import OrderRepositoryProtocol
from tuned.repository.protocols.order_delivery import OrderDeliveryRepositoryProtocol
from tuned.repository.protocols.payment import (
    PaymentsManagerProtocol, InvoiceManagerProtocol, TransactionManagerProtocol,
    DiscountManagerProtocol, RefundManagerProtocol, AcceptedMethodManagerProtocol,
    PaymentRepositoryProtocol
)
from tuned.repository.protocols.preferences import PreferenceRepositoryProtocol
from tuned.repository.protocols.price import (
    PricingCategoryRepositoryProtocol, PriceRateRepositoryProtocol
)
from tuned.repository.protocols.media import MediaRepositoryProtocol

__all__ = [
    "UserRepositoryProtocol",
    "ReferralRepositoryProtocol",
    "BlogRepositoryProtocol",
    "AcademicLevelRepositoryProtocol",
    "DeadlineRepositoryProtocol",
    "FAQRepositoryProtocol",
    "SampleRepositoryProtocol",
    "ServiceCategoryRepositoryProtocol",
    "ServiceRepositoryProtocol",
    "TestimonialRepositoryProtocol",
    "ActivityLogRepositoryProtocol",
    "EmailLogRepositoryProtocol",
    "OrderStatusHistoryRepositoryProtocol",
    "PriceHistoryRepositoryProtocol",
    "OrderRepositoryProtocol",
    "OrderDeliveryRepositoryProtocol",
    "PaymentsManagerProtocol",
    "InvoiceManagerProtocol",
    "TransactionManagerProtocol",
    "DiscountManagerProtocol",
    "RefundManagerProtocol",
    "AcceptedMethodManagerProtocol",
    "PaymentRepositoryProtocol",
    "PreferenceRepositoryProtocol",
    "PricingCategoryRepositoryProtocol",
    "PriceRateRepositoryProtocol",
    "MediaRepositoryProtocol"
]
