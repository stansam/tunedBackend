from __future__ import annotations

import uuid
import os
import logging
from typing import Optional, TYPE_CHECKING
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from flask import current_app
from dataclasses import asdict
from tuned.utils.variables import Variables
from tuned.core.logging import get_logger
from tuned.models.enums import FileType, DeliveryStatus, OrderStatus

from tuned.dtos.order_delivery import (
    CreateOrderDeliveryDTO,
    OrderDeliveryFileDTO,
    UpdateOrderDeliveryStatusDTO,
    AddDeliveryFilesDTO,
    OrderDeliveryResponseDTO,
)
from tuned.dtos.audit import ActivityLogCreateDTO

if TYPE_CHECKING:
    from tuned.repository import Repository
    from tuned.interface import Services
    from tuned.interface.protocols import ActivityLogServiceProtocol

logger: logging.Logger = get_logger(__name__)

class OrderDeliveryService:
    def __init__(
        self,
        repos: "Repository",
        interfaces: "Services",
        audit_service: Optional["ActivityLogServiceProtocol"] = None,
    ) -> None:
        self._repos = repos
        self._interfaces = interfaces
        self._repo = repos.order_delivery

        from tuned.interface.audit import AuditService as AuditAggregator
        self._audit = AuditAggregator(repos=repos)
        self._audit_service = audit_service or self._audit.activity_log

    def _process_and_save_files(
        self,
        order_id: str,
        files: list[FileStorage],
        file_type: FileType,
        delivery_id: str
    ) -> list[OrderDeliveryFileDTO]:
        from tuned.models.enums import AssetOwnerType
        
        file_dtos: list[OrderDeliveryFileDTO] = []
        for file in files:
            if not file or not file.filename:
                continue

            media_asset_dto = self._interfaces.media.upload_file(
                file=file,
                owner_type=AssetOwnerType.DELIVERY,
                owner_id=delivery_id,
                is_public=False
            )

            file_dtos.append(OrderDeliveryFileDTO(
                filename=media_asset_dto.original_filename,
                original_filename=media_asset_dto.original_filename,
                file_path=media_asset_dto.storage_path,
                file_size=media_asset_dto.file_size_bytes or 0,
                file_type=file_type,
                file_format=media_asset_dto.asset_type,
                asset_id=media_asset_dto.id
            ))
            
        return file_dtos

    def create_delivery(
        self,
        order_id: str,
        delivery_files: list[FileStorage],
        plagiarism_reports: list[FileStorage],
        user_id: str,
        ip_address: str,
        user_agent: str,
    ) -> OrderDeliveryResponseDTO:
        delivery_id = str(uuid.uuid4()) # TODO Check on this smells a bit
        all_file_dtos: list[OrderDeliveryFileDTO] = []
        
        try:
            all_file_dtos.extend(
                self._process_and_save_files(order_id, delivery_files, FileType.DELIVERY, delivery_id)
            )
            all_file_dtos.extend(
                self._process_and_save_files(order_id, plagiarism_reports, FileType.PLAGIARISM_REPORT, delivery_id)
            )

            create_dto = CreateOrderDeliveryDTO(
                id=delivery_id,
                order_id=order_id,
                delivery_files=all_file_dtos,
            )
            delivery_resp = self._repo.create_order_delivery(create_dto)

            order = self._repos.order.update_order_status(order_id, OrderStatus.COMPLETED_PENDING_REVIEW)

            self._audit_service.log(ActivityLogCreateDTO(
                user_id=user_id,
                action=Variables.ORDER_DELIVERED,
                entity_type=Variables.ORDER_DELIVERY_ENTITY_TYPE,
                entity_id=str(delivery_resp.id),
                after=delivery_resp,
                ip_address=ip_address,
                user_agent=user_agent,
            ))
            self._repo.save()

            response = OrderDeliveryResponseDTO.from_model(delivery_resp)

            from tuned.core.events import get_event_bus
            get_event_bus().emit(
                "delivery.created",
                {
                    "client_id": user_id,
                    "order_id": order_id,
                    "order_number": order.order_number,
                    "delivery": asdict(response),
                }
            )

            return response

        except Exception as exc:
            self._repo.rollback()
            for f in all_file_dtos:
                upload_root = current_app.config.get("UPLOAD_ROOT", "/tmp")
                abs_path = os.path.join(upload_root, f.file_path)
                if os.path.exists(abs_path):
                    try:
                        os.remove(abs_path)
                    except Exception as cleanup_exc:
                        logger.error(f"Failed to cleanup file {abs_path}: {cleanup_exc}")
            raise exc

    def get_deliveries_by_order(self, order_id: str) -> list[OrderDeliveryResponseDTO]:
        deliveries = self._repo.get_order_deliveries(order_id)
        return [OrderDeliveryResponseDTO.from_model(d) for d in deliveries] 

    def get_delivery_by_id(self, delivery_id: str) -> OrderDeliveryResponseDTO:
        delivery = self._repo.get_by_id(delivery_id)
        return OrderDeliveryResponseDTO.from_model(delivery)

    def add_delivery_files(
        self,
        delivery_id: str,
        order_id: str,
        delivery_files: list[FileStorage],
        plagiarism_reports: list[FileStorage],
        user_id: str,
        ip_address: str,
        user_agent: str,
    ) -> OrderDeliveryResponseDTO:
        all_file_dtos: list[OrderDeliveryFileDTO] = []
        
        try:
            # Process and save new files
            all_file_dtos.extend(
                self._process_and_save_files(order_id, delivery_files, FileType.DELIVERY, delivery_id)
            )
            all_file_dtos.extend(
                self._process_and_save_files(order_id, plagiarism_reports, FileType.PLAGIARISM_REPORT, delivery_id)
            )

            add_dto = AddDeliveryFilesDTO(delivery_files=all_file_dtos)
            delivery_resp = self._repo.add_files(delivery_id, add_dto)

            self._audit_service.log(ActivityLogCreateDTO(
                user_id=user_id,
                action=Variables.ORDER_DELIVERY_FILE_UPLOADED_ACTION,
                entity_type=Variables.ORDER_DELIVERY_ENTITY_TYPE,
                entity_id=delivery_id,
                ip_address=ip_address,
                user_agent=user_agent,
            ))
            self._repo.save()

            response = OrderDeliveryResponseDTO.from_model(delivery_resp)
            from tuned.core.events import get_event_bus
            get_event_bus().emit(
                "delivery.files_added",
                {
                    "client_id": user_id,
                    "delivery_id": delivery_id,
                    "delivery": asdict(response),
                }
            )

            return response

        except Exception as exc:
            self._repo.rollback()
            for f in all_file_dtos:
                upload_root = current_app.config.get("UPLOAD_ROOT", "/tmp")
                abs_path = os.path.join(upload_root, f.file_path)
                if os.path.exists(abs_path):
                    try:
                        os.remove(abs_path)
                    except Exception as cleanup_exc:
                        logger.error(f"Failed to cleanup file {abs_path}: {cleanup_exc}")
            raise exc

    def update_delivery_status(
        self,
        delivery_id: str,
        dto: UpdateOrderDeliveryStatusDTO,
        user_id: str,
        ip_address: str,
        user_agent: str,
    ) -> OrderDeliveryResponseDTO:
        try:
            delivery_resp = self._repo.update_status(delivery_id, dto)

            self._audit_service.log(ActivityLogCreateDTO(
                user_id=user_id,
                action=Variables.ORDER_DELIVERY_UPDATED,
                entity_type=Variables.ORDER_DELIVERY_ENTITY_TYPE,
                entity_id=delivery_id,
                after=delivery_resp,
                ip_address=ip_address,
                user_agent=user_agent,
            ))
            self._repo.save()

            response = OrderDeliveryResponseDTO.from_model(delivery_resp)

            from tuned.core.events import get_event_bus
            get_event_bus().emit(
                "delivery.status_changed",
                {
                    "client_id": user_id,
                    "delivery_id": delivery_id,
                    "delivery": asdict(response),
                }
            )

            return response
        except Exception as exc:
            self._repo.rollback()
            raise exc

    def mark_client_notified(self, delivery_id: str) -> OrderDeliveryResponseDTO:
        try:
            delivery_resp = self._repo.mark_client_notified(delivery_id)
            self._repo.save()
            return OrderDeliveryResponseDTO.from_model(delivery_resp)
        except Exception as exc:
            self._repo.rollback()
            raise exc

    def delete_delivery(
        self,
        delivery_id: str,
        user_id: str,
        ip_address: str,
        user_agent: str,
    ) -> None:
        try:
            delivery = self._repo.get_by_id(delivery_id)
            
            self._repo.delete(delivery_id, user_id)

            self._audit_service.log(ActivityLogCreateDTO(
                user_id=user_id,
                action=Variables.ORDER_DELIVERY_DELETED,
                entity_type=Variables.ORDER_DELIVERY_ENTITY_TYPE,
                entity_id=delivery_id,
                after=delivery,
                ip_address=ip_address,
                user_agent=user_agent,
            ))

            self._repo.save()

            from tuned.core.events import get_event_bus
            get_event_bus().emit(
                "delivery.deleted",
                {
                    "client_id": user_id,
                    "delivery_id": delivery_id,
                }
            )

        except Exception as exc:
            self._repo.rollback()
            raise exc
