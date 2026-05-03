from datetime import datetime, timezone
from typing import TYPE_CHECKING, Tuple, Optional
from tuned.models import Deadline
from tuned.dtos import(
    PriceRateLookupDTO, CalculatePriceRequestDTO, 
    CalculatePriceResponseDTO, DeadlineResponseDTO
)
from tuned.repository.exceptions import NotFound, DatabaseError

if TYPE_CHECKING:
    from tuned.interface import Services

class CalculatePriceService:
    def __init__(self, interfaces: "Services", words_per_page: int = 275) -> None:
        self._price_service = interfaces.price_rate
        self._price_category_service = interfaces.pricing_category
        self._deadline_service = interfaces.deadline
        self._academic_level_service = interfaces.academic_level
        self._words_per_page = words_per_page
    
    def _validate_lookup_data(self, data: PriceRateLookupDTO) -> bool:
        try:
            self._price_category_service.get_category(data.pricing_category_id)
            self._deadline_service.get_deadline(data.deadline_id)
            self._academic_level_service.get_academic_level(data.academic_level_id)
            return True
        except NotFound as e:
            raise NotFound(f"Price rate validation failed: {str(e)}.")
        except DatabaseError as e:
            raise DatabaseError(f"Database error while validating price rate: {str(e)}.")
        except Exception as e:
            raise Exception(f"Error while validating price rate: {str(e)}.")

    def _calculate_hours(self, deadline: datetime) -> float:
        return (deadline - datetime.now(timezone.utc)).total_seconds() / 3600
    
    def _match_deadline(self, hours: float) -> Tuple[DeadlineResponseDTO, str]:
        deadlines = self._deadline_service.list_deadlines()
        if not deadlines:
            raise NotFound("No deadlines configured.")
            
        selected_deadline = deadlines[-1] # Default to the longest deadline
        
        for deadline in deadlines:
            if hours <= (deadline.hours + 1):
                selected_deadline = deadline
                break
        
        return selected_deadline, str(selected_deadline.id)
    
    def _calculate_page_count(self, word_count: int) -> float:
        return max(1.0, round(word_count / self._words_per_page, 2))
    
    def _calculate_page_price(self, data: PriceRateLookupDTO, page_count: float) -> Tuple[float, float]:
        try:
            if self._validate_lookup_data(data):
                price_rate = self._price_service.lookup_rate(data)
                price_per_page = price_rate.price_per_page
                page_price = price_per_page * page_count
                return float(page_price), float(price_per_page)
            raise NotFound("Price rate validation failed.")
        except NotFound as e:
            raise NotFound(f"Page price not found: {str(e)}.")
        except DatabaseError as e:
            raise DatabaseError(f"Database error while fetching page price: {str(e)}.")
        except Exception as e:
            raise Exception(f"Error while fetching page price: {str(e)}.")
    
    def _get_report_price(self, report_type: str) -> float:
        if report_type == "standard":
            return 4.99
        elif report_type == "turnitin":
            return 9.99
        else:
            return 0.0

    def execute(self, data: CalculatePriceRequestDTO) -> CalculatePriceResponseDTO:
        try:
            hours = self._calculate_hours(data.deadline)
            selected_deadline, deadline_id = self._match_deadline(hours)
            lookup_dto = PriceRateLookupDTO(
                pricing_category_id=data.pricing_category_id,
                academic_level_id=data.academic_level_id,
                deadline_id=deadline_id
            )
            page_count = self._calculate_page_count(data.word_count)
            pages_price, price_per_page = self._calculate_page_price(lookup_dto, page_count)
            
            report_price = 0.0
            if data.report_type:
                report_price = self._get_report_price(data.report_type)
            
            total_price = pages_price + report_price

            return CalculatePriceResponseDTO(
                price_per_page=price_per_page,
                page_count=page_count,
                pages_price=pages_price,
                total_price=total_price,
                deadline_hours=round(hours, 2),
                selected_deadline=selected_deadline
            )
        except NotFound as e:
            raise NotFound(f"Price calculation failed: {str(e)}.")
        except DatabaseError as e:
            raise DatabaseError(f"Database error while calculating price: {str(e)}.")
        except Exception as e:
            raise Exception(f"Error while calculating price: {str(e)}.")
