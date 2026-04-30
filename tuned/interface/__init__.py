from tuned.interface.users import UserService
from tuned.interface.referral import ReferralInterface
from tuned.interface.content import (
    AcademicLevelService, DeadlineService, FAQService, SampleService,
    ServiceCategoryService, ServiceService, TestimonialService
)
from tuned.interface.price import PriceRateService, PricingCategoryService
from tuned.interface.blogs import(
    BlogCategoryService,
    BlogPostService,
    BlogCommentService,
    CommentReactionService
)
from tuned.interface.notification import NotificationInterface
from tuned.interface.order import OrderService
from tuned.interface.preferences.service import PreferenceService
from tuned.interface.analytics import AnalyticsService
from tuned.interface.audit import AuditService
from typing import Optional, TYPE_CHECKING

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
        self._blog_category: Optional[BlogCategoryService] = None
        self._blog_post: Optional[BlogPostService] = None
        self._blog_comment: Optional[BlogCommentService] = None
        self._comment_reaction: Optional[CommentReactionService] = None
        self._price_rate: Optional[PriceRateService] = None
        self._pricing_category: Optional[PricingCategoryService] = None
        self._notification: Optional[NotificationInterface] = None
        self._order: Optional[OrderService] = None
        self._preferences: Optional[PreferenceService] = None
        self._analytics: Optional[AnalyticsService] = None
        self._audit: Optional[AuditService] = None

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
    def blog_post(self) -> BlogPostService:
        if not self._blog_post:
            self._blog_post = BlogPostService()
        return self._blog_post

    @property
    def blog_category(self) -> BlogCategoryService:
        if not self._blog_category:
            self._blog_category = BlogCategoryService()
        return self._blog_category
    
    @property
    def blog_comment(self) -> BlogCommentService:
        if not self._blog_comment:
            self._blog_comment = BlogCommentService()
        return self._blog_comment
    
    @property
    def comment_reaction(self) -> CommentReactionService:
        if not self._comment_reaction:
            self._comment_reaction = CommentReactionService()
        return self._comment_reaction

    @property
    def price_rate(self) -> PriceRateService:
        if not self._price_rate:
            self._price_rate = PriceRateService(self)
        return self._price_rate

    @property
    def pricing_category(self) -> PricingCategoryService:
        if not self._pricing_category:
            self._pricing_category = PricingCategoryService()
        return self._pricing_category

    @property
    def notification(self) -> NotificationInterface:
        if not self._notification:
            self._notification = NotificationInterface()
        return self._notification

    @property
    def order(self) -> OrderService:
        if not self._order:
            self._order = OrderService()
        return self._order

    @property
    def preferences(self) -> PreferenceService:
        if not self._preferences:
            self._preferences = PreferenceService()
        return self._preferences

    @property
    def analytics(self) -> AnalyticsService:
        if not self._analytics:
            self._analytics = AnalyticsService()
        return self._analytics

    @property
    def audit(self) -> AuditService:
        if not self._audit:
            self._audit = AuditService(repos=self._repos)
        return self._audit


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
