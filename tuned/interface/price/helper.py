from datetime import datetime, timezone
from typing import TYPE_CHECKING
from flask import current_app
from tuned.models import Deadline
from tuned.dtos import(
    PriceRateLookupDTO, CalculatePriceRequestDTO, 
    CalculatePriceResponseDTO, CalculatePriceRequestDTO, DeadlineResponseDTO
)
from tuned.repository.exceptions import NotFound, DatabaseError

if TYPE_CHECKING:
    from tuned.interface import Services

class CalculatePriceService:
    def __init__(self, interfaces:"Services" ) -> None:
        self._price_service = interfaces.price_rate
        self._price_category_service = interfaces.pricing_category
        self._deadline_service = interfaces.deadline
        self._academic_level_service = interfaces.academic_level
    
    def _validate_lookup_data(self, data: PriceRateLookupDTO) -> bool:
        try:
            price_category = self._price_category_service.get_category(data.pricing_category_id)
            deadline = self._deadline_service.get_deadline(data.deadline_id)
            academic_level = self._academic_level_service.get_academic_level(data.academic_level_id)
            return True
        except NotFound as e:
            raise NotFound(f"Price rate not found: {str(e)}.")
        except DatabaseError as e:
            raise DatabaseError(f"Database error while fetching price rate: {str(e)}.")
        except Exception as e:
            raise Exception(f"Error while fetching price rate: {str(e)}.")
    def _calculate_hours(self, deadline: datetime) -> int:
        return (deadline - datetime.now(timezone.utc)).total_seconds() / 3600
    
    def _match_deadline(self, hours: int) -> (Deadline, str):
        deadline_id = None
        selected_deadline = None

        deadlines = self._deadline_service.list_deadlines()        
        for deadline in deadlines:
            if hours <= (deadline.hours + 1):
                deadline_id = deadline.id
                selected_deadline = deadline
                break
        
        if deadline_id is None:
            selected_deadline = deadlines[-1]
            deadline_id = selected_deadline.id
        return selected_deadline, deadline_id
    
    def _calculate_page_count(self, word_count: int) -> int:
        words_per_page = current_app.config.get("WORDS_PER_PAGE", 275)
        return max(1, round(word_count / words_per_page, 2))
    
    def _calculate_page_price(self, data: PriceRateLookupDTO, page_count: int) -> (int, int):
        try:
            price_rate = None
            if self._validate_lookup_data(data):
                price_rate = self._price_service.lookup_rate(data)

            price_per_page = price_rate.price_per_page
            page_price = price_per_page * page_count
            return page_price, price_per_page
        except NotFound as e:
            raise NotFound(f"Page price not found: {str(e)}.")
        except DatabaseError as e:
            raise DatabaseError(f"Database error while fetching page price: {str(e)}.")
        except Exception as e:
            raise Exception(f"Error while fetching page price: {str(e)}.")
    
    def _get_report_price(self, report_type: str) -> int:
        if report_type == "standard":
            return 4.99
        elif report_type == "turnitin":
            return 9.99
        else:
            return 0

    
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
            
            report_price = 0
            if data.report_type:
                report_price = self._get_report_price(data.report_type)
            
            total_price = pages_price + report_price

            response = CalculatePriceResponseDTO(
                price_per_page=price_per_page,
                page_count=page_count,
                pages_price=pages_price,
                total_price=total_price,
                deadline_hours=round(hours, 2),
                selected_deadline=DeadlineResponseDTO.from_model(selected_deadline)
            )
            return response
        except NotFound as e:
            raise NotFound(f"Price calculation failed: {str(e)}.")
        except DatabaseError as e:
            raise DatabaseError(f"Database error while calculating price: {str(e)}.")
        except Exception as e:
            raise Exception(f"Error while calculating price: {str(e)}.")      
            


