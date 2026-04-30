from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from tuned.interface.analytics.client import AnalyticsService

if TYPE_CHECKING:
    from tuned.repository import Repository

class Analytics:
    def __init__(self, repos: Repository) -> None:
        self._repos = repos
        self._client: AnalyticsService | None = None

    @property
    def client(self) -> AnalyticsService:
        if not self._client:
            self._client = AnalyticsService(repos=self._repos)
        return self._client

__all__ = [
    'Analytics',
    'AnalyticsService',
]
