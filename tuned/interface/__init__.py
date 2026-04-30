from typing import Optional, TYPE_CHECKING
from tuned.interface.users import UserService
from tuned.interface.referral import ReferralInterface
from tuned.interface.content import (
    AcademicLevelService, DeadlineService, FAQService, SampleService,
    ServiceCategoryService, ServiceService, TestimonialService
)
from tuned.interface.price import PriceRateService, PricingCategoryService
from tuned.interface.blogs import Blogs, BlogPostService, BlogCategoryService, BlogCommentService, CommentReactionService
from tuned.interface.notification import NotificationInterface
from tuned.interface.order import OrderService
from tuned.interface.preferences.service import PreferenceService
from tuned.interface.analytics import Analytics, AnalyticsService
from tuned.interface.audit import AuditService
from tuned.interface.payment import PaymentService

if TYPE_CHECKING:
    from tuned.repository import Repository

class Services:
    def __init__(self, repos: Optional["Repository"] = None) -> None:
        self._repos = repos
        self._user: Optional[UserService] = None
        self._referral: Optional[ReferralInterface] = None
        self._academic_level: Optional[AcademicLevelService] = None
        self._deadline: Optional[DeadlineService] = None
        self._service: Optional[ServiceService] = None
        self._service_category: Optional[ServiceCategoryService] = None
        self._sample: Optional[SampleService] = None
        self._testimonial: Optional[TestimonialService] = None
        self._faq: Optional[FAQService] = None
        self._blogs: Optional[Blogs] = None
        self._price_rate: Optional[PriceRateService] = None
        self._pricing_category: Optional[PricingCategoryService] = None
        self._notification: Optional[NotificationInterface] = None
        self._order: Optional[OrderService] = None
        self._preferences: Optional[PreferenceService] = None
        self._analytics_agg: Optional[Analytics] = None
        self._audit: Optional[AuditService] = None
        self._payment: Optional[PaymentService] = None

    @property
    def user(self) -> UserService:
        if not self._user:
            self._user = UserService(repos=self._repos)
        return self._user
    
    @property
    def referral(self) -> ReferralInterface:
        if not self._referral:
            self._referral = ReferralInterface(repos=self._repos)
        return self._referral

    @property
    def academic_level(self) -> AcademicLevelService:
        if not self._academic_level:
            self._academic_level = AcademicLevelService(repos=self._repos)
        return self._academic_level

    @property
    def deadline(self) -> DeadlineService:
        if not self._deadline:
            self._deadline = DeadlineService(repos=self._repos)
        return self._deadline

    @property
    def faq(self) -> FAQService:
        if not self._faq:
            self._faq = FAQService(repos=self._repos)
        return self._faq

    @property
    def sample(self) -> SampleService:
        if not self._sample:
            self._sample = SampleService(repos=self._repos)
        return self._sample

    @property
    def service(self) -> ServiceService:
        if not self._service:
            self._service = ServiceService(repos=self._repos)
        return self._service

    @property
    def service_category(self) -> ServiceCategoryService:
        if not self._service_category:
            self._service_category = ServiceCategoryService(repos=self._repos)
        return self._service_category

    @property
    def testimonial(self) -> TestimonialService:
        if not self._testimonial:
            self._testimonial = TestimonialService(repos=self._repos)
        return self._testimonial

    @property
    def blogs(self) -> Blogs:
        if not self._blogs:
            self._blogs = Blogs(repos=self._repos)
        return self._blogs

    @property
    def blog_post(self) -> BlogPostService:
        return self.blogs.post

    @property
    def blog_category(self) -> BlogCategoryService:
        return self.blogs.category
    
    @property
    def blog_comment(self) -> BlogCommentService:
        return self.blogs.comment
    
    @property
    def comment_reaction(self) -> CommentReactionService:
        return self.blogs.reaction

    @property
    def price_rate(self) -> PriceRateService:
        if not self._price_rate:
            self._price_rate = PriceRateService(interfaces=self, repos=self._repos)
        return self._price_rate

    @property
    def pricing_category(self) -> PricingCategoryService:
        if not self._pricing_category:
            self._pricing_category = PricingCategoryService(repos=self._repos)
        return self._pricing_category

    @property
    def notification(self) -> NotificationInterface:
        if not self._notification:
            self._notification = NotificationInterface(repos=self._repos)
        return self._notification

    @property
    def order(self) -> OrderService:
        if not self._order:
            self._order = OrderService(repos=self._repos)
        return self._order

    @property
    def preferences(self) -> PreferenceService:
        if not self._preferences:
            self._preferences = PreferenceService(repos=self._repos)
        return self._preferences

    @property
    def analytics_agg(self) -> Analytics:
        if not self._analytics_agg:
            self._analytics_agg = Analytics(repos=self._repos)
        return self._analytics_agg

    @property
    def analytics(self) -> AnalyticsService:
        return self.analytics_agg.client

    @property
    def audit(self) -> AuditService:
        if not self._audit:
            self._audit = AuditService(repos=self._repos)
        return self._audit

    @property
    def payment(self) -> PaymentService:
        if not self._payment:
            self._payment = PaymentService(repos=self._repos)
        return self._payment


# Global instance for legacy support.
# DEPRECATED: Do not use in new code. Use dependency injection instead.
from tuned.repository import repositories
interface = Services(repos=repositories)
user = interface.user
referral = interface.referral
academic_level = interface.academic_level
deadline = interface.deadline
service = interface.service
service_category = interface.service_category
sample = interface.sample
testimonial = interface.testimonial
faq = interface.faq
blogs_agg = interface.blogs
blog_category = interface.blog_category
blog_post = interface.blog_post
blog_comment = interface.blog_comment
comment_reaction = interface.comment_reaction
price_rate = interface.price_rate
pricing_category = interface.pricing_category
notification = interface.notification
order = interface.order
preferences = interface.preferences
analytics = interface.analytics
payment = interface.payment
audit = interface.audit
