import logging

from tuned.dtos import SampleDTO, SampleResponseDTO, SampleListRequestDTO, SampleListResponseDTO
from tuned.repository import repositories
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound
from tuned.core.logging import get_logger

logger: logging.Logger = get_logger(__name__)


class SampleService:
    def __init__(self) -> None:
        self._repo = repositories.sample

    def create_sample(self, data: SampleDTO) -> SampleResponseDTO:
        try:
            logger.info("Creating sample: %s", data.title)
            result = self._repo.create(data)
            logger.info("Sample created: id=%s slug=%s", result.id, result.slug)
            return result
        except AlreadyExists:
            logger.error("Sample already exists: %s", data.title)
            raise AlreadyExists("Sample already exists")
        except DatabaseError:
            logger.error("Failed to create sample: %s", data.title)
            raise DatabaseError("Failed to create sample")

    def get_sample(self, sample_id: str) -> SampleResponseDTO:
        try:
            return self._repo.get_by_id(sample_id)
        except NotFound:
            logger.error("Sample not found: %s", sample_id)
            raise NotFound("Sample not found")
        except DatabaseError:
            logger.error("Failed to get sample: %s", sample_id)
            raise DatabaseError("Failed to get sample")

    def get_sample_by_slug(self, slug: str) -> SampleResponseDTO:
        try:
            return self._repo.get_by_slug(slug)
        except NotFound:
            logger.error("Sample not found: %s", slug)
            raise NotFound("Sample not found")
        except DatabaseError:
            logger.error("Failed to get sample: %s", slug)
            raise DatabaseError("Failed to get sample")
    
    def list_featured_samples(self) -> list[SampleResponseDTO]:
        try:
            return self._repo.get_featured()
        except DatabaseError:
            logger.error("Failed to get featured samples")
            raise DatabaseError("Failed to get featured samples")

    def list_samples(
        self,
        req: SampleListRequestDTO
    ) -> SampleListResponseDTO:
        try:
            return self._repo.get_all(req)
        except DatabaseError:
            logger.error("Failed to get samples")
            raise DatabaseError("Failed to get samples")

    def update_sample(self, sample_id: str, updates: dict) -> SampleResponseDTO:
        try:
            allowed = {"title", "content", "excerpt", "service_id",
                    "word_count", "featured", "image", "slug"}
            safe_updates = {k: v for k, v in updates.items() if k in allowed}
            logger.info("Updating sample id=%s fields=%s", sample_id, list(safe_updates.keys()))
            result = self._repo.update(sample_id, safe_updates)
            logger.info("Sample updated: id=%s", sample_id)
            return result
        except NotFound:
            logger.error("Sample not found: %s", sample_id)
            raise NotFound("Sample not found")
        except DatabaseError:
            logger.error("Failed to update sample: %s", sample_id)
            raise DatabaseError("Failed to update sample")

    def delete_sample(self, sample_id: str) -> None:
        try:
            logger.info("Deleting sample id=%s", sample_id)
            self._repo.delete(sample_id)
            logger.info("Sample deleted: id=%s", sample_id)
        except NotFound:
            logger.error("Sample not found: %s", sample_id)
            raise NotFound("Sample not found")
        except DatabaseError:
            logger.error("Failed to delete sample: %s", sample_id)
            raise DatabaseError("Failed to delete sample")

    def get_samples_by_service_id(self, service_id: str) -> list[SampleResponseDTO]:
        try:
            return self._repo.get_samples_by_service_id(service_id)
        except DatabaseError:
            logger.error("Failed to get samples by service id: %s", service_id)
            raise DatabaseError("Failed to get samples by service id")
            
