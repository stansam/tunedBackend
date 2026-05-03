from __future__ import annotations
import logging
from typing import Optional, TYPE_CHECKING
from tuned.dtos import (
    PriceRateDTO,
    PriceRateResponseDTO,
    PriceRateUpdateDTO,
    PriceRateLookupDTO,
    CalculatePriceRequestDTO,
    CalculatePriceResponseDTO,
)
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound
from tuned.interface.price.helper import CalculatePriceService
from tuned.core.logging import get_logger

if TYPE_CHECKING:
    from tuned.interface import Services
    from tuned.repository import Repository
    from tuned.repository.protocols import PriceRateRepositoryProtocol

logger: logging.Logger = get_logger(__name__)

class PriceRateService:
    def __init__(self, interfaces: Services, repos: Repository) -> None:
        self._repo = repos.price_rate
        self._interfaces = interfaces

    def create_rate(self, data: PriceRateDTO) -> PriceRateResponseDTO:
        try:
            logger.info(
                "Creating price rate: category=%s level=%s deadline=%s price=%.2f",
                data.pricing_category_id,
                data.academic_level_id,
                data.deadline_id,
                data.price_per_page,
            )
            result = self._repo.create(data)
            logger.info("Price rate created: id=%s", result.id)
            return result
        except AlreadyExists:
            logger.error("Price rate already exists for category %s", data.pricing_category_id)
            raise AlreadyExists("Price rate already exists")
        except DatabaseError:
            logger.error("Database error while creating price rate")
            raise DatabaseError("Database error while creating price rate")

    def get_rate(self, rate_id: str) -> PriceRateResponseDTO:
        try:
            return self._repo.get_by_id(rate_id)
        except NotFound:
            logger.error("Price rate not found: %s", rate_id)
            raise NotFound("Price rate not found")
        except DatabaseError:
            logger.error("Database error while fetching price rate")
            raise DatabaseError("Database error while fetching price rate")

    def lookup_rate(self, lookup: PriceRateLookupDTO) -> PriceRateResponseDTO:
        try:
            return self._repo.get_by_dimensions(lookup)
        except NotFound:
            logger.error("Price rate not found: %s", lookup)
            raise NotFound("Price rate not found")
        except DatabaseError:
            logger.error("Database error while fetching price rate")
            raise DatabaseError("Database error while fetching price rate")

    def list_rates_by_category(
        self, pricing_category_id: str, active_only: bool = True
    ) -> list[PriceRateResponseDTO]:
        try:
            return list(self._repo.get_by_category(pricing_category_id, active_only))
        except DatabaseError:
            logger.error("Database error while fetching price rate")
            raise DatabaseError("Database error while fetching price rate")

    def update_rate(self, rate_id: str, data: PriceRateUpdateDTO) -> PriceRateResponseDTO:
        try:
            logger.info("Updating price rate id=%s", rate_id)
            result = self._repo.update(rate_id, data)
            logger.info("Price rate updated: id=%s", rate_id)
            return result
        except NotFound:
            logger.error("Price rate not found: %s", rate_id)
            raise NotFound("Price rate not found")
        except DatabaseError:
            logger.error("Database error while updating price rate")
            raise DatabaseError("Database error while updating price rate")

    def delete_rate(self, rate_id: str) -> None:
        try:
            logger.info("Deleting price rate id=%s", rate_id)
            self._repo.delete(rate_id)
            logger.info("Price rate deleted: id=%s", rate_id)
        except NotFound:
            logger.error("Price rate not found: %s", rate_id)
            raise NotFound("Price rate not found")
        except DatabaseError:
            logger.error("Database error while deleting price rate")
            raise DatabaseError("Database error while deleting price rate")
    
    def calculate_price(self, data: CalculatePriceRequestDTO) -> CalculatePriceResponseDTO:
        try:
            logger.info("Calculating price for data=%s", data)
            return CalculatePriceService(self._interfaces).execute(data)
        except NotFound:
            logger.error("Price rate not found: %s", data)
            raise NotFound("Price rate not found")
        except DatabaseError:
            logger.error("Database error while calculating price")
            raise DatabaseError("Database error while calculating price")
