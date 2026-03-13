from tuned.interface.users import UserService
from tuned.interface.content import(
    AcademicLevelService, DeadlineService, FAQService, SampleService, 
    ServiceCategoryService, ServiceService, TestimonialService
)

from tuned.interface.price import PriceRateService, PricingCategoryService

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
        self._price_rate = None
        self._pricing_category = None

    @property
    def user(self) -> UserService:
        if not self._user:
            self._user = UserService
        return self._user

    @property
    def academic_level(self) -> AcademicLevelService:
        if not self._academic_level:
            self._academic_level = AcademicLevelService
        return self._academic_level

    @property
    def deadline(self) -> DeadlineService:
        if not self._deadline:
            self._deadline = DeadlineService
        return self._deadline

    @property
    def faq(self) -> FAQService:
        if not self._faq:
            self._faq = FAQService
        return self._faq

    @property
    def sample(self) -> SampleService:
        if not self._sample:
            self._sample = SampleService
        return self._sample

    @property
    def service(self) -> ServiceService:
        if not self._service:
            self._service = ServiceService
        return self._service

    @property
    def service_category(self) -> ServiceCategoryService:
        if not self._service_category:
            self._service_category = ServiceCategoryService
        return self._service_category

    @property
    def testimonial(self) -> TestimonialService:
        if not self._testimonial:
            self._testimonial = TestimonialService
        return self._testimonial

    @property
    def price_rate(self) -> PriceRateService:
        if not self._price_rate:
            self._price_rate = PriceRateService
        return self._price_rate

    @property
    def pricing_category(self) -> PricingCategoryService:
        if not self._pricing_category:
            self._pricing_category = PricingCategoryService
        return self._pricing_category

    
