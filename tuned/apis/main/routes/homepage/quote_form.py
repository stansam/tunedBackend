from flask.views import MethodView
from tuned.utils.dependencies import get_services
from tuned.apis.main.schemas import CalculatePriceSchema
from tuned.utils.responses import success_response, error_response
from tuned.redis_client import redis_client
from tuned.dtos import CalculatePriceRequestDTO, ServiceWithPricingCategory
from tuned.utils.enums import PricingCategoryEnum
from tuned.core.logging import get_logger

from marshmallow import ValidationError
from flask.views import MethodView
from dataclasses import asdict
from flask import request
import json
import logging
from typing import Any

logger: logging.Logger = get_logger(__name__)

CACHE_KEY = 'quote:options'
CACHE_TTL = 600

class GetQuoteFormOptions(MethodView):    
    def _build_services_response(self) -> list[ServiceWithPricingCategory]:
        services = get_services().service.list_services()
        services_response: list[ServiceWithPricingCategory] = []
        
        for service in services:
            category_name = service.category.name
            pricing_name = (
                (service.pricing_category.name).lower() 
                if service.pricing_category else None
            )

            pricing_enum = PricingCategoryEnum.from_string(pricing_name)
            

            services_response.append(
                ServiceWithPricingCategory(
                    id = service.id,
                    name = service.name,
                    category = category_name,
                    pricing_category = pricing_enum.value
                )
            )

        return services_response

    def get(self) -> tuple[Any, int]:
        try:
            cached_data = redis_client.get(CACHE_KEY)
            if cached_data:
                logger.debug('Returning quote form options from cache')
                return success_response(json.loads(cached_data))
            
            # TODO: Implement strict response DTOs
            services = self._build_services_response()     
            academic_levels = get_services().academic_level.list_academic_levels()
            
            data = {
                'services': [asdict(s) for s in services],
                'levels': [asdict(a) for a in academic_levels],
            }
            
            redis_client.setex(
                CACHE_KEY,
                CACHE_TTL,
                json.dumps(data)
            )
            
            logger.info('Quote form options fetched and cached successfully')
            return success_response(data)
        
        except ValidationError as err:
            logger.error(f'Validation error: {str(err)}')
            return error_response(
                'Invalid data provided',
                status=400,
                details=err.messages
            )
            
        except Exception as e:
            logger.error(f'Error fetching quote form options: {str(e)}')
            return error_response(
                'Failed to fetch form options',
                status=500
            )

class CalculatePrice(MethodView):
    def __init__(self):
        self._schema = CalculatePriceSchema()
    
    def _convert_schema_to_dto(self, data: dict) -> CalculatePriceRequestDTO:
        data = data.copy()
        data.pop("service_id", None)

        return CalculatePriceRequestDTO(
            deadline=data.get('deadline'),
            pricing_category_id=data.get('pricing_category_id'),
            academic_level_id=data.get('level_id'),
            word_count=data.get('word_count'),
            report_type=data.get('report_type', None)
        )
    def _get_service_pricing_category(self, service_id: int) -> int:
        from tuned.repository.exceptions import DatabaseError, NotFound
        try:
            service = get_services().service.get_service(service_id)
            return service.pricing_category_id
        except NotFound as e:
            raise NotFound(f"Service not found: {str(e)}.") from e
        except DatabaseError as e:
            raise DatabaseError(f"Database error while fetching service: {str(e)}.") from e
        except Exception as e:
            raise RuntimeError(f"Error while fetching service category: {str(e)}.") from e
        

    def post(self) -> tuple[Any, int]:
        try:
            data = request.get_json()
            validated_data = self._schema.load(data)

            service_category_id = self._get_service_pricing_category(validated_data['service_id'])
            validated_data['pricing_category_id'] = service_category_id

            dto = self._convert_schema_to_dto(validated_data)
            price = get_services().price_rate.calculate_price(dto)

            return success_response(price)

        except ValidationError as err:
            logger.error(f'Validation error: {str(err)}')
            return error_response(
                'Invalid data provided',
                status=400,
                errors=err.messages
            )
        except Exception as e:
            logger.error(f'Error calculating price: {str(e)}')
            return error_response(
                'Failed to calculate price',
                status=500
            )
