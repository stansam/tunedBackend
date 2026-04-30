from typing import List, TYPE_CHECKING
from tuned.dtos.content import TagResponseDTO

if TYPE_CHECKING:
    from tuned.repository import Repository

class TagService:
    def __init__(self, repos: "Repository") -> None:
        self._repos = repos

    def list_tags(self, limit: int = 20) -> List[TagResponseDTO]:
        tags = self._repos.tag.list_tags(limit=limit)
        return [TagResponseDTO.from_model(tag) for tag in tags]

    def get_tag_by_slug(self, slug: str) -> TagResponseDTO | None:
        tag = self._repos.tag.get_tag_by_slug(slug)
        if not tag:
            return None
        return TagResponseDTO.from_model(tag)
