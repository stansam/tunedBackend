from dataclasses import dataclass, field
from typing import List, Optional, Any
from tuned.dtos.base import BaseDTO

@dataclass
class SearchResultItemDTO:
    id: str
    type: str
    title: str
    slug: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    service: Optional[str] = None
    published_at: Optional[str] = None
    usage_count: Optional[int] = None
    question: Optional[str] = None
    answer: Optional[str] = None

@dataclass
class SearchCountsDTO:
    services: int = 0
    samples: int = 0
    blogs: int = 0
    faqs: int = 0
    tags: int = 0
    total: int = 0

@dataclass
class SearchResponseDTO:
    query: str
    type: str
    results: dict[str, List[dict[str, Any]]]
    counts: SearchCountsDTO
