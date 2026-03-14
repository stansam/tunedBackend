from tuned.repository.user import UserRepository
from tuned.repository.blogs import BlogRepository
from tuned.repository.content import(
    AcademicLevelRepository, DeadlineRepository, ServiceRepository, ServiceCategoryRepository,
    SampleRepository, TestimonialRepository, FAQRepository
)
from tuned.repository.price import (
    PricingCategoryRepository, PriceRateRepository
)
class Repository:
    def __init__(self):
        self._user = None
        self._blog = None
        self._academic_level = None
        self._deadline = None
        self._service = None
        self._service_category = None
        self._sample = None
        self._testimonial = None
        self._faq = None
        self._price = None
        self._pricing_category = None

    @property
    def user(self) -> UserRepository:
        if not self._user:
            self._user = UserRepository()
        return self._user

    @property
    def blog(self) -> BlogRepository:
        if not self._blog:
            self._blog = BlogRepository()
        return self._blog
    
    @property
    def academic_level(self) -> AcademicLevelRepository:
        if not self._academic_level:
            self._academic_level = AcademicLevelRepository()
        return self._academic_level
    
    @property
    def deadline(self) -> DeadlineRepository:
        if not self._deadline:
            self._deadline = DeadlineRepository()
        return self._deadline
    
    @property
    def service(self) -> ServiceRepository:
        if not self._service:
            self._service = ServiceRepository()
        return self._service
    
    @property
    def service_category(self) -> ServiceCategoryRepository:
        if not self._service_category:
            self._service_category = ServiceCategoryRepository()
        return self._service_category
    
    @property
    def sample(self) -> SampleRepository:
        if not self._sample:
            self._sample = SampleRepository()
        return self._sample
    
    @property
    def testimonial(self) -> TestimonialRepository:
        if not self._testimonial:
            self._testimonial = TestimonialRepository()
        return self._testimonial
    
    @property
    def faq(self) -> FAQRepository:
        if not self._faq:
            self._faq = FAQRepository()
        return self._faq
    
    @property
    def price_rate(self) -> PriceRateRepository:
        if not self._price:
            self._price = PriceRateRepository()
        return self._price
    
    @property
    def pricing_category(self) -> PricingCategoryRepository:
        if not self._pricing_category:
            self._pricing_category = PricingCategoryRepository()
        return self._pricing_category


repositories = Repository()