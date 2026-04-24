from __future__ import annotations
import logging
from tuned.core.logging import get_logger
from tuned.dtos.audit import ActivityLogCreateDTO
from tuned.core.exceptions import NotFound
from tuned.dtos.payment import AcceptedMethodCreateDTO, AcceptedMethodUpdateDTO, AcceptedMethodResponseDTO
from tuned.interface.audit import audit_service
from tuned.repository import repositories
from tuned.utils.variables import Variables

logger: logging.Logger = get_logger(__name__)

class AdminCreateAcceptedMethod:
    def __init__(self) -> None:
        self._repo = repositories.payment.accepted_method
        self._audit = audit_service

    def execute(self, data: AcceptedMethodCreateDTO, admin_id: str) -> AcceptedMethodResponseDTO:
        try:
            method = self._repo.create(data)

            try:
                self._audit.activity_log.log(ActivityLogCreateDTO(
                    action=Variables.ACCEPTED_METHOD_CREATE_ACTION,
                    user_id=admin_id,
                    entity_type=Variables.PAYMENT_ENTITY_TYPE,
                    entity_id=method.id,
                    after=method,
                    created_by=admin_id,
                ))
            except Exception as audit_exc:
                logger.error(f"[AdminCreateAcceptedMethod] Audit failed for method {method.id}: {audit_exc!r}")

            logger.info(f"[AdminCreateAcceptedMethod] Accepted payment method {method.name} created by admin {admin_id}")
            return method
        except Exception as exc:
            logger.error(f"[AdminCreateAcceptedMethod] Failed to create method: {exc!r}")
            raise

class AdminUpdateAcceptedMethod:
    def __init__(self) -> None:
        self._repo = repositories.payment.accepted_method
        self._audit = audit_service

    def execute(self, method_id: str, data: AcceptedMethodUpdateDTO, admin_id: str) -> AcceptedMethodResponseDTO:
        try:
            try:
                existing = self._repo.get_by_id(method_id)
            except NotFound:
                logger.error(f"[AdminUpdateAcceptedMethod] Accepted payment method {method_id} not found")
                raise NotFound("Accepted method not found")
            method = self._repo.update(existing.id, data)

            try:
                self._audit.activity_log.log(ActivityLogCreateDTO(
                    action=Variables.ACCEPTED_METHOD_UPDATE_ACTION,
                    user_id=admin_id,
                    entity_type=Variables.PAYMENT_ENTITY_TYPE,
                    entity_id=existing.id,
                    before=existing,
                    after=method,
                    created_by=admin_id,
                ))
            except Exception as audit_exc:
                logger.error(f"[AdminUpdateAcceptedMethod] Audit failed for method {method.id}: {audit_exc!r}")

            logger.info(f"[AdminUpdateAcceptedMethod] Accepted payment method {method.id} updated by admin {admin_id}")
            return method
        except Exception as exc:
            logger.error(f"[AdminUpdateAcceptedMethod] Failed to update method {method_id}: {exc!r}")
            raise

class GetAcceptedMethods:
    def __init__(self) -> None:
        self._repo = repositories.payment.accepted_method

    def execute(self) -> list[AcceptedMethodResponseDTO]:
        try:
            return self._repo.get_all_active()
        except Exception as exc:
            logger.error(f"[GetAcceptedMethods] Failed to fetch active methods: {exc!r}")
            raise
