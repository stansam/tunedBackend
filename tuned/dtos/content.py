from typing import Optional

class DeadlineDTO:
    name: str
    hours: int
    order: int

class AcademicLevelDTO:
    name: str
    order: int

class SampleDTO:
    title: str
    content: str
    excerpt: str
    service_id: str
    word_count: int
    featured: bool
    image: str
    slug: Optional[str] = None

class TestimonialDTO:
    user_id: str
    service_id: str
    order_id: str
    content: str
    rating: int
    is_approved: Optional[bool] = False

class FaqDTO:
    question: str
    answer: str
    category: str
    order: int