from tuned.repository.user import UserRepository
from tuned.repository.referral import ReferralRepository
from tuned.repository.blogs import BlogRepository
from tuned.repository.content import(
    AcademicLevelRepository, DeadlineRepository, ServiceRepository, ServiceCategoryRepository,
    SampleRepository, TestimonialRepository, FAQRepository
)
from tuned.repository.price import (
    PricingCategoryRepository, PriceRateRepository
)
from tuned.repository.audit import AuditRepository
from tuned.repository.order import OrderRepository
from tuned.repository.preferences import PreferenceRepository
from tuned.repository.payment import PaymentRepository
from tuned.extensions import db
from sqlalchemy.orm import Session

class Repository:
    def __init__(self) -> None:
        self._user: UserRepository | None = None
        self._referral: ReferralRepository | None = None
        self._blog: BlogRepository | None = None
        self._academic_level: AcademicLevelRepository | None = None
        self._deadline: DeadlineRepository | None = None
        self._service: ServiceRepository | None = None
        self._service_category: ServiceCategoryRepository | None = None
        self._sample: SampleRepository | None = None
        self._testimonial: TestimonialRepository | None = None
        self._faq: FAQRepository | None = None
        self._price: PriceRateRepository | None = None
        self._pricing_category: PricingCategoryRepository | None = None
        self._audit: AuditRepository | None = None
        self._order: OrderRepository | None = None
        self._preferences: PreferenceRepository | None = None
        self._payment: PaymentRepository | None = None

    @property
    def user(self) -> UserRepository:
        if not self._user:
            self._user = UserRepository(db.session)  # type: ignore[arg-type]
        return self._user
    
    @property
    def referral(self) -> ReferralRepository:
        if not self._referral:
            self._referral = ReferralRepository(db.session)  # type: ignore[arg-type]
        return self._referral

    @property
    def blog(self) -> BlogRepository:
        if not self._blog:
            self._blog = BlogRepository(db.session)  # type: ignore[arg-type]
        return self._blog
    
    @property
    def academic_level(self) -> AcademicLevelRepository:
        if not self._academic_level:
            self._academic_level = AcademicLevelRepository(db.session)  # type: ignore[arg-type]
        return self._academic_level
    
    @property
    def deadline(self) -> DeadlineRepository:
        if not self._deadline:
            self._deadline = DeadlineRepository(db.session)  # type: ignore[arg-type]
        return self._deadline
    
    @property
    def service(self) -> ServiceRepository:
        if not self._service:
            self._service = ServiceRepository(db.session)  # type: ignore[arg-type]
        return self._service
    
    @property
    def service_category(self) -> ServiceCategoryRepository:
        if not self._service_category:
            self._service_category = ServiceCategoryRepository(db.session)  # type: ignore[arg-type]
        return self._service_category
    
    @property
    def sample(self) -> SampleRepository:
        if not self._sample:
            self._sample = SampleRepository(db.session)  # type: ignore[arg-type]
        return self._sample
    
    @property
    def testimonial(self) -> TestimonialRepository:
        if not self._testimonial:
            self._testimonial = TestimonialRepository(db.session)  # type: ignore[arg-type]
        return self._testimonial
    
    @property
    def faq(self) -> FAQRepository:
        if not self._faq:
            self._faq = FAQRepository(db.session)  # type: ignore[arg-type]
        return self._faq
    
    @property
    def price_rate(self) -> PriceRateRepository:
        if not self._price:
            self._price = PriceRateRepository(db.session)  # type: ignore[arg-type]
        return self._price

    @property
    def pricing_category(self) -> PricingCategoryRepository:
        if not self._pricing_category:
            self._pricing_category = PricingCategoryRepository(db.session)  # type: ignore[arg-type]
        return self._pricing_category

    @property
    def audit(self) -> AuditRepository:
        if not self._audit:
            self._audit = AuditRepository(db.session)  # type: ignore[arg-type]
        return self._audit

    @property
    def order(self) -> OrderRepository:
        if not self._order:
            self._order = OrderRepository(db.session)  # type: ignore[arg-type]
        return self._order

    @property
    def preferences(self) -> PreferenceRepository:
        if not self._preferences:
            self._preferences = PreferenceRepository(db.session)  # type: ignore[arg-type]
        return self._preferences

    @property
    def payment(self) -> PaymentRepository:
        if not self._payment:
            self._payment = PaymentRepository(db.session)  # type: ignore[arg-type]
        return self._payment


repositories = Repository()