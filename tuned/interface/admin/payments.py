from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from tuned.core.logging import get_logger
from tuned.dtos.payment import AdminPaymentListResponseDTO, AdminPaymentListRequestDTO

if TYPE_CHECKING:
    from tuned.repository import Repository

logger = get_logger(__name__)

class AdminPaymentService:
    def __init__(self, repos: "Repository") -> None:
        self._repos = repos

    def list_payments(self, req: AdminPaymentListRequestDTO) -> AdminPaymentListResponseDTO:
        try:
            payments, total = self._repos.admin_payments.list_payments(
                status=req.status,
                q=req.q,
                page=req.page,
                per_page=req.per_page
            )
            return AdminPaymentListResponseDTO(
                payments=payments,
                total=total,
                page=req.page,
                per_page=req.per_page
            )
        except Exception as exc:
            logger.error("[AdminPaymentService] list_payments failed: %s", exc)
            raise
