from tuned.dtos.base import BaseDTO, PaginationDTO
from dataclasses import dataclass
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from tuned.models.service import AcademicLevel, Deadline, Service
    from tuned.models.content import Sample, Testimonial, FAQ
    from tuned.models.tag import Tag


@dataclass
class DeadlineDTO(BaseDTO):
    name: str
    hours: int
    order: int = 0


@dataclass
class AcademicLevelDTO(BaseDTO):
    name: str
    order: int = 0


@dataclass
class SampleDTO(BaseDTO):
    title: str
    content: str
    service_id: str
    excerpt: str = ""
    word_count: int = 0
    featured: bool = False
    image: str = ""
    slug: Optional[str] = None


@dataclass
class TestimonialDTO(BaseDTO):
    user_id: str
    service_id: str
    content: str
    rating: int
    order_id: Optional[str] = None
    is_approved: bool = False


@dataclass
class FaqDTO(BaseDTO):
    question: str
    answer: str
    category: str = "General"
    order: int = 0

@dataclass
class TagDTO(BaseDTO):
    name: str
    description: str
    slug: str
    usage_count: int

@dataclass
class AcademicLevelResponseDTO(BaseDTO):
    id: str
    name: str
    order: int

    @classmethod
    def from_model(cls, obj: "AcademicLevel") -> "AcademicLevelResponseDTO":
        return cls(
            id=obj.id,
            name=obj.name,
            order=obj.order,
        )

@dataclass
class DeadlineResponseDTO(BaseDTO):
    id: str
    name: str
    hours: int
    order: int

    @classmethod
    def from_model(cls, obj: "Deadline") -> "DeadlineResponseDTO":
        return cls(
            id=obj.id,
            name=obj.name,
            hours=obj.hours,
            order=obj.order,
        )

@dataclass
class SampleServiceResponseDTO:
    id: str
    name: str
    slug: str

    @classmethod
    def from_model(cls, obj: "Service") -> "SampleServiceResponseDTO":
        return cls(
            id=obj.id,
            name=obj.name,
            slug=obj.slug,
        )
    

@dataclass
class SampleResponseDTO(BaseDTO):
    id: str
    title: str
    slug: str
    excerpt: str
    service_id: str
    word_count: int
    featured: bool
    image: str
    tags: List[TagResponseDTO]
    service: SampleServiceResponseDTO

    @classmethod
    def from_model(cls, obj: "Sample") -> "SampleResponseDTO":
        return cls(
            id=obj.id,
            title=obj.title,
            slug=obj.slug,
            excerpt=obj.excerpt or "",
            service_id=obj.service_id,
            word_count=obj.word_count or 0,
            featured=obj.featured,
            image=obj.image or "",
            tags=[TagResponseDTO.from_model(tag) for tag in obj.tag_list.all()],
            service=SampleServiceResponseDTO.from_model(obj.service),
        )

@dataclass
class SampleListResponseDTO(PaginationDTO):
    samples: List[SampleResponseDTO]
    total: int

    @classmethod
    def from_model(cls, obj: "Sample") -> "SampleListResponseDTO":
        return cls(
            samples=[SampleResponseDTO.from_model(sample) for sample in obj.samples],
            total=obj.total,
            sort=obj.sort,
            order=obj.order,
            page=obj.page,
            per_page=obj.per_page,
        )

@dataclass
class SampleListRequestDTO(PaginationDTO):
    q: Optional[str] = None
    service_id: Optional[str] = None
    featured: Optional[bool] = None
    
@dataclass
class TestimonialResponseDTO(BaseDTO):
    id: str
    user_id: str
    service_id: str
    order_id: str
    content: str
    rating: int
    is_approved: bool

    @classmethod
    def from_model(cls, obj: "Testimonial") -> "TestimonialResponseDTO":
        return cls(
            id=obj.id,
            user_id=obj.user_id,
            service_id=obj.service_id,
            order_id=obj.order_id,
            content=obj.content,
            rating=obj.rating,
            is_approved=obj.is_approved,
        )


@dataclass
class FaqResponseDTO(BaseDTO):
    id: str
    question: str
    answer: str
    category: str
    order: int

    @classmethod
    def from_model(cls, obj: "FAQ") -> "FaqResponseDTO":
        return cls(
            id=obj.id,
            question=obj.question,
            answer=obj.answer,
            category=obj.category,
            order=obj.order,
        )

@dataclass
class TagResponseDTO(BaseDTO):
    id: str
    name: str
    description: str
    slug: str
    usage_count: int

    @classmethod
    def from_model(cls, obj: "Tag") -> "TagResponseDTO":
        return cls(
            id=obj.id,
            name=obj.name,
            description=obj.description,
            slug=obj.slug,
            usage_count=obj.usage_count,
        )