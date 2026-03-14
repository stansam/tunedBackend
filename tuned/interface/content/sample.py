import logging

from tuned.dtos import SampleDTO, SampleResponseDTO
from tuned.repository import repositories
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound

logger = logging.getLogger(__name__)


class SampleService:
    """Service layer for Sample (writing work examples) business logic."""

    def __init__(self) -> None:
        self._repo = repositories.sample

    def create_sample(self, data: SampleDTO) -> SampleResponseDTO:
        """Create a new sample piece.

        Raises:
            AlreadyExists: If a sample with this title or slug already exists.
            DatabaseError: On unexpected database failure.
        """
        logger.info("Creating sample: %s", data.title)
        result = self._repo.create(data)
        logger.info("Sample created: id=%s slug=%s", result.id, result.slug)
        return result

    def get_sample(self, sample_id: str) -> SampleResponseDTO:
        """Retrieve a sample by ID.

        Raises:
            NotFound: If no sample exists with the given ID.
            DatabaseError: On unexpected database failure.
        """
        return self._repo.get_by_id(sample_id)

    def get_sample_by_slug(self, slug: str) -> SampleResponseDTO:
        """Retrieve a sample by its URL slug.

        Raises:
            NotFound: If no sample exists with the given slug.
            DatabaseError: On unexpected database failure.
        """
        return self._repo.get_by_slug(slug)
    
    def list_featured_samples(self) -> list[SampleResponseDTO]:
        return self._repo.get_featured()

    def list_samples(
        self,
        service_id: str | None = None,
        featured_only: bool = False,
    ) -> list[SampleResponseDTO]:
        """Return samples, optionally filtered by service or featured flag.

        Raises:
            DatabaseError: On unexpected database failure.
        """
        return self._repo.get_all(service_id=service_id, featured_only=featured_only)

    def update_sample(self, sample_id: str, updates: dict) -> SampleResponseDTO:
        """Update mutable fields of a sample.

        Raises:
            NotFound: If no sample exists with the given ID.
            AlreadyExists: If the update would cause a title/slug conflict.
            DatabaseError: On unexpected database failure.
        """
        allowed = {"title", "content", "excerpt", "service_id",
                   "word_count", "featured", "image", "slug"}
        safe_updates = {k: v for k, v in updates.items() if k in allowed}
        logger.info("Updating sample id=%s fields=%s", sample_id, list(safe_updates.keys()))
        result = self._repo.update(sample_id, safe_updates)
        logger.info("Sample updated: id=%s", sample_id)
        return result

    def delete_sample(self, sample_id: str) -> None:
        """Permanently delete a sample.

        Raises:
            NotFound: If no sample exists with the given ID.
            DatabaseError: On unexpected database failure.
        """
        logger.info("Deleting sample id=%s", sample_id)
        self._repo.delete(sample_id)
        logger.info("Sample deleted: id=%s", sample_id)
