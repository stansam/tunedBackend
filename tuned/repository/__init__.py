from tuned.repository.user import UserRepository
from tuned.repository.referral import ReferralRepository
from tuned.repository.blogs import BlogRepository
from tuned.repository.content import(
    AcademicLevelRepository, DeadlineRepository, ServiceRepository, ServiceCategoryRepository,
    SampleRepository, TestimonialRepository, FAQRepository, TagRepository
)
from tuned.repository.price import (
    PricingCategoryRepository, PriceRateRepository
)
from tuned.repository.audit import AuditRepository
from tuned.repository.order import OrderRepository
from tuned.repository.preferences import PreferenceRepository
from tuned.repository.payment import PaymentRepository
from tuned.repository.communication import NewsletterRepository
from tuned.repository.user.notification import NotificationRepository
from tuned.extensions import db
from sqlalchemy.orm import Session, scoped_session
from typing import Optional, Union, Any

class Repository:
    def __init__(self, session: Any) -> None:
        self.session = session
        self._user: Optional[UserRepository] = None
        self._referral: Optional[ReferralRepository] = None
        self._blog: Optional[BlogRepository] = None
        self._academic_level: Optional[AcademicLevelRepository] = None
        self._deadline: Optional[DeadlineRepository] = None
        self._service: Optional[ServiceRepository] = None
        self._service_category: Optional[ServiceCategoryRepository] = None
        self._sample: Optional[SampleRepository] = None
        self._testimonial: Optional[TestimonialRepository] = None
        self._faq: Optional[FAQRepository] = None
        self._price: Optional[PriceRateRepository] = None
        self._pricing_category: Optional[PricingCategoryRepository] = None
        self._audit: Optional[AuditRepository] = None
        self._order: Optional[OrderRepository] = None
        self._preferences: Optional[PreferenceRepository] = None
        self._payment: Optional[PaymentRepository] = None
        self._notification: Optional[NotificationRepository] = None
        self._tag: Optional[TagRepository] = None
        self._newsletter: Optional[NewsletterRepository] = None

    @property
    def user(self) -> UserRepository:
        if not self._user:
            self._user = UserRepository(self.session)
        return self._user
    
    @property
    def referral(self) -> ReferralRepository:
        if not self._referral:
            self._referral = ReferralRepository(self.session)
        return self._referral

    @property
    def blog(self) -> BlogRepository:
        if not self._blog:
            self._blog = BlogRepository(self.session)
        return self._blog
    
    @property
    def academic_level(self) -> AcademicLevelRepository:
        if not self._academic_level:
            self._academic_level = AcademicLevelRepository(self.session)
        return self._academic_level
    
    @property
    def deadline(self) -> DeadlineRepository:
        if not self._deadline:
            self._deadline = DeadlineRepository(self.session)
        return self._deadline
    
    @property
    def service(self) -> ServiceRepository:
        if not self._service:
            self._service = ServiceRepository(self.session)
        return self._service
    
    @property
    def service_category(self) -> ServiceCategoryRepository:
        if not self._service_category:
            self._service_category = ServiceCategoryRepository(self.session)
        return self._service_category
    
    @property
    def sample(self) -> SampleRepository:
        if not self._sample:
            self._sample = SampleRepository(self.session)
        return self._sample
    
    @property
    def testimonial(self) -> TestimonialRepository:
        if not self._testimonial:
            self._testimonial = TestimonialRepository(self.session)
        return self._testimonial
    
    @property
    def faq(self) -> FAQRepository:
        if not self._faq:
            self._faq = FAQRepository(self.session)
        return self._faq
    
    @property
    def price_rate(self) -> PriceRateRepository:
        if not self._price:
            self._price = PriceRateRepository(self.session)
        return self._price

    @property
    def pricing_category(self) -> PricingCategoryRepository:
        if not self._pricing_category:
            self._pricing_category = PricingCategoryRepository(self.session)
        return self._pricing_category

    @property
    def audit(self) -> AuditRepository:
        if not self._audit:
            self._audit = AuditRepository(self.session)
        return self._audit

    @property
    def order(self) -> OrderRepository:
        if not self._order:
            self._order = OrderRepository(self.session)
        return self._order

    @property
    def preferences(self) -> PreferenceRepository:
        if not self._preferences:
            self._preferences = PreferenceRepository(self.session)
        return self._preferences

    @property
    def payment(self) -> PaymentRepository:
        if not self._payment:
            self._payment = PaymentRepository(self.session)
        return self._payment

    @property
    def notification(self) -> NotificationRepository:
        if not self._notification:
            self._notification = NotificationRepository(self.session)
        return self._notification

    @property
    def tag(self) -> TagRepository:
        if not self._tag:
            self._tag = TagRepository(self.session)
        return self._tag

    @property
    def newsletter(self) -> NewsletterRepository:
        if not self._newsletter:
            self._newsletter = NewsletterRepository(self.session)
        return self._newsletter
