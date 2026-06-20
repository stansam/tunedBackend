from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from tuned.interface.analytics.client import AnalyticsService
from tuned.interface.analytics.admin import AdminAnalyticsService

if TYPE_CHECKING:
    from tuned.repository import Repository
    from tuned.interface import Services

class Analytics:
    def __init__(self, repos: Repository, interfaces: Services) -> None:
        self._repos = repos
        self._interfaces = interfaces
        self._client: AnalyticsService | None = None
        self._admin: AdminAnalyticsService | None = None

    @property
    def client(self) -> AnalyticsService:
        if not self._client:
            self._client = AnalyticsService(repos=self._repos)
        return self._client
    
    @property
    def admin(self) -> AdminAnalyticsService:
        if not self._admin:
            self._admin = AdminAnalyticsService(repos=self._repos, interfaces=self._interfaces)
        return self._admin

__all__ = [
    'Analytics',
]
