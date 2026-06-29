import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func, delete
from datetime import datetime, timedelta, timezone

from tuned.models.search_analytics import SearchSession, SearchEvent, SearchClick, PopularSearch

class SearchAnalyticsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()

    def get_or_create_session(self, session_key: str, user_id: Optional[str] = None, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> SearchSession:
        stmt = select(SearchSession).where(SearchSession.session_key == session_key)
        search_session = self.session.scalar(stmt)
        if not search_session:
            uid = uuid.UUID(user_id) if user_id else None
            search_session = SearchSession(
                user_id=uid,
                session_key=session_key,
                ip_address=ip_address,
                user_agent=user_agent
            )
            self.session.add(search_session)
            self.session.flush()
        else:
            if user_id and not search_session.user_id:
                search_session.user_id = uuid.UUID(user_id)
                self.session.flush()
        return search_session

    def log_event(self, query: str, search_type: str, session_key: Optional[str], user_id: Optional[str], result_count: int, device_type: Optional[str], ip_address: Optional[str], source: str) -> SearchEvent:
        session_id = None
        if session_key:
            s_session = self.get_or_create_session(session_key, user_id, ip_address, device_type)
            session_id = s_session.id
            
        uid = uuid.UUID(user_id) if user_id else None
        event = SearchEvent(
            query_text=query.lower().strip(),
            search_type=search_type,
            session_id=session_id,
            user_id=uid,
            result_count=result_count,
            device_type=device_type,
            ip_address=ip_address,
            source=source
        )
        self.session.add(event)
        self.session.flush()
        return event

    def log_click(self, event_id: str, clicked_entity_type: str, clicked_entity_id: str, position: int) -> SearchClick:
        click = SearchClick(
            search_event_id=uuid.UUID(event_id),
            clicked_entity_type=clicked_entity_type,
            clicked_entity_id=uuid.UUID(clicked_entity_id),
            position=position
        )
        self.session.add(click)
        self.session.flush()
        return click

    def record_popular_search(self, query: str) -> None:
        clean_query = query.strip().lower()
        if len(clean_query) < 2:
            return
            
        stmt = select(PopularSearch).where(PopularSearch.query_text == clean_query)
        pop = self.session.scalar(stmt)
        if pop:
            pop.search_count += 1
            pop.last_searched_at = datetime.now(timezone.utc)
        else:
            pop = PopularSearch(query_text=clean_query, search_count=1)
            self.session.add(pop)
        self.session.flush()

    def get_popular_searches(self, limit: int = 5) -> List[PopularSearch]:
        stmt = select(PopularSearch).order_by(PopularSearch.search_count.desc()).limit(limit)
        return list(self.session.scalars(stmt).all())

    def get_trending_searches(self, limit: int = 5, days: int = 7) -> List[str]:
        # Simple velocity: number of search events for this query in the last 'days'
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = (
            select(SearchEvent.query_text, func.count(SearchEvent.id).label('velocity'))
            .where(SearchEvent.created_at >= cutoff)
            .group_by(SearchEvent.query_text)
            .order_by(func.count(SearchEvent.id).desc())
            .limit(limit)
        )
        rows = self.session.execute(stmt).all()
        return [row[0] for row in rows]

    def purge_old_events(self, days: int = 90) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Cascades will delete clicks automatically if we delete events
        stmt = delete(SearchEvent).where(SearchEvent.created_at < cutoff)
        res = self.session.execute(stmt)
        
        # Also clean up sessions with no search events
        session_stmt = delete(SearchSession).where(
            ~SearchSession.id.in_(
                select(SearchEvent.session_id).where(SearchEvent.session_id.is_not(None))
            )
        )
        self.session.execute(session_stmt)
        
        self.session.flush()
        return getattr(res, "rowcount", 0)
