from dataclasses import dataclass, field
from typing import Optional


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
    order_id: str
    content: str
    rating: int
    is_approved: Optional[bool] = False


@dataclass
class FaqDTO:
    question: str
    answer: str
    category: str = "General"
    order: int = 0