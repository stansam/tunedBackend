from __future__ import annotations
from typing import TYPE_CHECKING
from tuned.core.logging import get_logger
from tuned.dtos.admin.users import (
    AdminUserListRequestDTO, AdminUserListResponseDTO,
    AdminUserStatsDTO, GeographicDistributionDTO,
)
from tuned.repository.admin.users import (
    GetAdminUserList, GetAdminUserStats, GetGeographicDistribution
)

if TYPE_CHECKING:
    from tuned.repository import Repository

logger = get_logger(__name__)


class AdminUserService:
    def __init__(self, repos: "Repository") -> None:
        self._repos = repos

    def list_users(self, req: AdminUserListRequestDTO) -> AdminUserListResponseDTO:
        return GetAdminUserList(self._repos.session).execute(req)

    def get_stats(self) -> AdminUserStatsDTO:
        return GetAdminUserStats(self._repos.session).execute()

    def get_geography(self) -> list[GeographicDistributionDTO]:
        return GetGeographicDistribution(self._repos.session).execute()

    def broadcast(self, message: str) -> dict:
        """Broadcast a message to all active clients via SocketIO."""
        try:
            from tuned.extensions import socketio
            socketio.emit("admin.broadcast", {"message": message})
            logger.info("[AdminUserService.broadcast] Broadcast sent: %s", message[:50])
        except Exception as exc:
            logger.error("[AdminUserService.broadcast] Failed: %r", exc)
            raise
        return {"success": True, "message": "Broadcast sent"}

    def message_user(self, user_id: str, message: str) -> dict:
        """Send a direct message to a specific user via SocketIO."""
        try:
            from tuned.extensions import socketio
            socketio.emit(
                "admin.direct_message",
                {"message": message},
                to=f"user_{user_id}",
            )
        except Exception as exc:
            logger.error("[AdminUserService.message_user] Failed: %r", exc)
            raise
        return {"success": True, "message": f"Message sent to user {user_id}"}
