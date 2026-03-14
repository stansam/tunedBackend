from dataclasses import dataclass
from typing import Optional, List


# ---------------------------------------------------------------------------
# Request DTOs
# ---------------------------------------------------------------------------

@dataclass
class DeadlineDTO:
    name: str
    hours: int
    order: int = 0


@dataclass
class AcademicLevelDTO:
    name: str
    order: int = 0


@dataclass
class SampleDTO:
    title: str
    content: str
    service_id: str
    excerpt: str = ""
    word_count: int = 0
    featured: bool = False
    image: str = ""
    slug: Optional[str] = None


@dataclass
class TestimonialDTO:
    user_id: str
    service_id: str
    content: str
    rating: int
    order_id: Optional[str] = None
    is_approved: bool = False


@dataclass
class FaqDTO:
    question: str
    answer: str
    category: str = "General"
    order: int = 0


# ---------------------------------------------------------------------------
# Response DTOs
# ---------------------------------------------------------------------------

@dataclass
class AcademicLevelResponseDTO:
    id: str
    name: str
    order: int

    @classmethod
    def from_model(cls, obj) -> "AcademicLevelResponseDTO":
        return cls(
            id=obj.id,
            name=obj.name,
            order=obj.order,
        )

@dataclass
class DeadlineResponseDTO:
    id: str
    name: str
    hours: int
    order: int

    @classmethod
    def from_model(cls, obj) -> "DeadlineResponseDTO":
        return cls(
            id=obj.id,
            name=obj.name,
            hours=obj.hours,
            order=obj.order,
        )

@dataclass
class SampleResponseDTO:
    id: str
    title: str
    slug: str
    excerpt: str
    service_id: str
    word_count: int
    featured: bool
    image: str

    @classmethod
    def from_model(cls, obj) -> "SampleResponseDTO":
        return cls(
            id=obj.id,
            title=obj.title,
            slug=obj.slug,
            excerpt=obj.excerpt or "",
            service_id=obj.service_id,
            word_count=obj.word_count or 0,
            featured=obj.featured,
            image=obj.image or "",
        )


@dataclass
class TestimonialResponseDTO:
    id: str
    user_id: str
    service_id: str
    order_id: str
    content: str
    rating: int
    is_approved: bool

    @classmethod
    def from_model(cls, obj) -> "TestimonialResponseDTO":
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
class FaqResponseDTO:
    id: str
    question: str
    answer: str
    category: str
    order: int

    @classmethod
    def from_model(cls, obj) -> "FaqResponseDTO":
        return cls(
            id=obj.id,
            question=obj.question,
            answer=obj.answer,
            category=obj.category,
            order=obj.order,
        )