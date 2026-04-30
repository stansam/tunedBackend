from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from tuned.interface.analytics.client import AnalyticsService

if TYPE_CHECKING:
    from tuned.repository import Repository

class Analytics:
    def __init__(self, repos: Optional[Repository] = None) -> None:
        self._repos = repos
        self._client: AnalyticsService | None = None

    @property
    def client(self) -> AnalyticsService:
        if not self._client:
            self._client = AnalyticsService(repos=self._repos)
        return self._client

# Legacy support
from tuned.repository import repositories
analytics = Analytics(repos=repositories)

__all__ = [
    'Analytics',
    'analytics',
    'AnalyticsService',
]
