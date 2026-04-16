from tuned.interface.users import UserService
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


class Services:
    def __init__(self) -> None:
        self._user = None
        self._academic_level = None
        self._deadline = None
        self._service = None
        self._service_category = None
        self._sample = None
        self._testimonial = None
        self._faq = None
        # self._blog = None
        self._blog_category = None
        self._blog_post = None
        self._blog_comment = None
        self._comment_reaction = None
        self._price_rate = None
        self._pricing_category = None
        self._notification = None

    @property
    def user(self) -> UserService:
        if not self._user:
            self._user = UserService()
        return self._user

    @property
    def academic_level(self) -> AcademicLevelService:
        if not self._academic_level:
            self._academic_level = AcademicLevelService()
        return self._academic_level

    @property
    def deadline(self) -> DeadlineService:
        if not self._deadline:
            self._deadline = DeadlineService()
        return self._deadline

    @property
    def faq(self) -> FAQService:
        if not self._faq:
            self._faq = FAQService()
        return self._faq

    @property
    def sample(self) -> SampleService:
        if not self._sample:
            self._sample = SampleService()
        return self._sample

    @property
    def service(self) -> ServiceService:
        if not self._service:
            self._service = ServiceService()
        return self._service

    @property
    def service_category(self) -> ServiceCategoryService:
        if not self._service_category:
            self._service_category = ServiceCategoryService()
        return self._service_category

    @property
    def testimonial(self) -> TestimonialService:
        if not self._testimonial:
            self._testimonial = TestimonialService()
        return self._testimonial

    # @property
    # def blog(self) -> BlogsService:
    #     if not self._blog:
    #         self._blog = BlogsService()
    #     return self._blog
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


interface = Services()
# services = interface.service
user = interface.user
academic_level = interface.academic_level
deadline = interface.deadline
service = interface.service
service_category = interface.service_category
sample = interface.sample
testimonial = interface.testimonial
faq = interface.faq
# blog = interface.blog
blog_category = interface.blog_category
blog_post = interface.blog_post
blog_comment = interface.blog_comment
comment_reaction = interface.comment_reaction
price_rate = interface.price_rate
pricing_category = interface.pricing_category
notification = interface.notification
