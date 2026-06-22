import uuid
from typing import List, Optional
import logging
from sqlalchemy import select
from tuned.core.logging import get_logger
from tuned.repository import Repository
from tuned.models.preferences.privacy import UserPrivacySettings

logger: logging.Logger = get_logger(__name__)

class SearchAnalyticsService:
    def __init__(self, repos: Repository) -> None:
        self._repos = repos

    def _should_track_analytics(self, user_id: Optional[str]) -> bool:
        if not user_id:
            return True
        try:
            uid = uuid.UUID(user_id)
            stmt = select(UserPrivacySettings).where(UserPrivacySettings.user_id == uid)
            privacy = self._repos.search_analytics.session.scalar(stmt)
            if privacy:
                return privacy.analytics_tracking
            return True
        except Exception as e:
            logger.warning(f"Error checking analytics preference for user {user_id}: {str(e)}")
            return True

    def track_search(
        self,
        query: str,
        search_type: str,
        session_key: Optional[str] = None,
        user_id: Optional[str] = None,
        result_count: int = 0,
        device_type: Optional[str] = None,
        ip_address: Optional[str] = None,
        source: str = 'hero'
    ) -> str:
        try:
            if not self._should_track_analytics(user_id):
                user_id = None
                session_key = None
                ip_address = None
            
            if ip_address:
                parts = ip_address.split('.')
                if len(parts) == 4:
                    ip_address = f"{parts[0]}.{parts[1]}.{parts[2]}.0"
                else:
                    ip_address = ip_address[:19] + ":0000"

            event = self._repos.search_analytics.log_event(
                query=query,
                search_type=search_type,
                session_key=session_key,
                user_id=user_id,
                result_count=result_count,
                device_type=device_type,
                ip_address=ip_address,
                source=source
            )
            
            self._repos.search_analytics.record_popular_search(query)
            self._repos.search_analytics.save()
            return str(event.id)
        except Exception as e:
            logger.error(f"Error tracking search event: {str(e)}")
            self._repos.search_analytics.rollback()
            return ""

    def track_click(
        self,
        event_id: str,
        clicked_type: str,
        clicked_id: str,
        position: int,
        user_id: Optional[str] = None
    ) -> str:
        try:
            if not self._should_track_analytics(user_id):
                return ""

            click = self._repos.search_analytics.log_click(
                event_id=event_id,
                clicked_entity_type=clicked_type,
                clicked_entity_id=clicked_id,
                position=position
            )
            self._repos.search_analytics.save()
            return str(click.id)
        except Exception as e:
            logger.error(f"Error tracking search click: {str(e)}")
            self._repos.search_analytics.rollback()
            return ""

    def get_popular(self, limit: int = 5) -> List[dict]:
        try:
            pops = self._repos.search_analytics.get_popular_searches(limit)
            return [
                {
                    "query": p.query_text,
                    "search_count": p.search_count,
                    "last_searched_at": p.last_searched_at.isoformat()
                }
                for p in pops
            ]
        except Exception as e:
            logger.error(f"Error getting popular searches: {str(e)}")
            return []

    def get_trending(self, limit: int = 5) -> List[str]:
        try:
            return self._repos.search_analytics.get_trending_searches(limit)
        except Exception as e:
            logger.error(f"Error getting trending searches: {str(e)}")
            return []

    def run_retention_purge(self, days: int = 90) -> int:
        try:
            purged = self._repos.search_analytics.purge_old_events(days)
            self._repos.search_analytics.save()
            return purged
        except Exception as e:
            logger.error(f"Error purging old search analytics: {str(e)}")
            self._repos.search_analytics.rollback()
            return 0
