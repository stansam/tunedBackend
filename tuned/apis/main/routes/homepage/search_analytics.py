from flask import request
from flask.views import MethodView
from flask_login import current_user
from marshmallow import ValidationError
from typing import Any
import logging

from tuned.utils.dependencies import get_services
from tuned.apis.main.schemas.search_analytics import TrackSearchEventSchema, TrackSearchClickSchema
from tuned.utils.responses import (
    success_response, 
    validation_error_response,
    error_response
)
from tuned.core.logging import get_logger

logger = get_logger(__name__)

class TrackSearchEventView(MethodView):
    def __init__(self) -> None:
        self._schema = TrackSearchEventSchema()

    def post(self) -> tuple[Any, int]:
        try:
            data = request.get_json() or {}
            params = self._schema.load(data)
            
            user_id = str(current_user.id) if current_user.is_authenticated else None
            ip_address = request.remote_addr
            
            event_id = get_services().search_analytics.track_search(
                query=params['query'],
                search_type=params.get('search_type', 'all'),
                session_key=params.get('session_key'),
                user_id=user_id,
                result_count=params.get('result_count', 0),
                device_type=params.get('device_type'),
                ip_address=ip_address,
                source=params.get('source', 'hero')
            )
            
            return success_response({"event_id": event_id}, "Search tracked successfully")
            
        except ValidationError as err:
            return validation_error_response(err.messages)
        except Exception as e:
            logger.error(f'Error tracking search event: {str(e)}')
            return error_response('Failed to track search event', status=500)

class TrackSearchClickView(MethodView):
    def __init__(self) -> None:
        self._schema = TrackSearchClickSchema()

    def post(self) -> tuple[Any, int]:
        try:
            data = request.get_json() or {}
            params = self._schema.load(data)
            
            user_id = str(current_user.id) if current_user.is_authenticated else None
            
            click_id = get_services().search_analytics.track_click(
                event_id=params['event_id'],
                clicked_type=params['clicked_type'],
                clicked_id=params['clicked_id'],
                position=params['position'],
                user_id=user_id
            )
            
            return success_response({"click_id": click_id}, "Search click tracked successfully")
            
        except ValidationError as err:
            return validation_error_response(err.messages)
        except Exception as e:
            logger.error(f'Error tracking search click: {str(e)}')
            return error_response('Failed to track search click', status=500)

class GetPopularSearchesView(MethodView):
    def get(self) -> tuple[Any, int]:
        try:
            limit = request.args.get('limit', 5, type=int)
            popular = get_services().search_analytics.get_popular(limit)
            return success_response(popular, "Popular searches fetched successfully")
        except Exception as e:
            logger.error(f'Error getting popular searches: {str(e)}')
            return error_response('Failed to fetch popular searches', status=500)

class GetTrendingSearchesView(MethodView):
    def get(self) -> tuple[Any, int]:
        try:
            limit = request.args.get('limit', 5, type=int)
            trending = get_services().search_analytics.get_trending(limit)
            return success_response(trending, "Trending searches fetched successfully")
        except Exception as e:
            logger.error(f'Error getting trending searches: {str(e)}')
            return error_response('Failed to fetch trending searches', status=500)
