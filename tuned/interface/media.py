from __future__ import annotations
import os
import uuid
import hashlib
import tempfile
import zipfile
import logging
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING, Any, List
from flask import current_app
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from tuned.core.exceptions import ValidationError, NotFound, ServiceError
from tuned.models.media import MediaAsset
from tuned.models.enums import AssetOwnerType
from tuned.dtos.media import MediaAssetCreateDTO, MediaAssetResponseDTO
from tuned.dtos.audit import ActivityLogCreateDTO
from tuned.repository.protocols.media import MediaRepositoryProtocol
from tuned.interface.protocols import ActivityLogServiceProtocol
from tuned.interface.order.util import resolve_file_type
from tuned.utils.variables import Variables
from tuned.core.logging import get_logger

if TYPE_CHECKING:
    from tuned.repository import Repository
    from tuned.interface import Services

logger = get_logger(__name__)


class MediaService:
    def __init__(
        self,
        repos: Repository,
        interfaces: Optional[Services] = None,
        repo: Optional[MediaRepositoryProtocol] = None,
        audit_service: Optional[ActivityLogServiceProtocol] = None
    ) -> None:
        self._repos = repos
        self._interfaces = interfaces
        self._repo = repos.media
        self._audit_service = audit_service
        
        if not self._audit_service and repos:
            from tuned.interface.audit import AuditService as AuditAggregator
            self._audit = AuditAggregator(repos=repos)
            self._audit_service = self._audit.activity_log

    def upload_file(
        self,
        file: FileStorage,
        owner_type: AssetOwnerType,
        owner_id: str,
        is_public: bool = True,
        alt_text: Optional[str] = None
    ) -> MediaAssetResponseDTO:
        if not file or not file.filename:
            raise ValidationError("No file provided")

        original_filename = secure_filename(file.filename)
        if not original_filename:
            raise ValidationError("Invalid filename")

        ext = os.path.splitext(original_filename)[1].lower().lstrip(".")
        file_format = resolve_file_type(ext)

        # Read file data to check size and compute checksum
        file_data = file.read()
        file.seek(0)  # Reset stream

        file_size = len(file_data)
        max_size = current_app.config.get("MAX_CONTENT_LENGTH", 16 * 1024 * 1024)
        if file_size > max_size:
            raise ValidationError(f"File size exceeds maximum allowed size of {max_size} bytes")

        checksum = hashlib.sha256(file_data).hexdigest()

        # Determine target subfolder
        if owner_type == AssetOwnerType.USER:
            subfolder = "profile_pics"
        elif owner_type == AssetOwnerType.BLOG_POST:
            subfolder = "blog"
        elif owner_type == AssetOwnerType.ORDER:
            subfolder = f"order_files/{owner_id}"
        elif owner_type == AssetOwnerType.DELIVERY:
            # Query delivery to find the order ID for path parity
            delivery = self._repos.order_delivery.get_by_id(owner_id)
            if not delivery:
                raise NotFound("Delivery not found")
            subfolder = f"order_deliveries/{delivery.order_id}"
        else:
            subfolder = "other"

        # Unique filename
        stored_filename = f"{uuid.uuid4()}{os.path.splitext(original_filename)[1]}"
        relative_path = f"{subfolder}/{stored_filename}"

        upload_root = current_app.config.get("UPLOAD_ROOT", current_app.instance_path)
        absolute_dir = os.path.join(upload_root, subfolder)
        os.makedirs(absolute_dir, exist_ok=True)
        absolute_file_path = os.path.join(absolute_dir, stored_filename)

        try:
            # Save file to disk
            with open(absolute_file_path, "wb") as f:
                f.write(file_data)

            create_dto = MediaAssetCreateDTO(
                original_filename=original_filename,
                storage_path=relative_path,
                asset_type=file_format,
                file_size_bytes=file_size,
                is_public=is_public,
                alt_text=alt_text,
                checksum_sha256=checksum,
                owner_type=owner_type,
                owner_id=owner_id
            )

            asset = self._repo.create(create_dto)
            
            # Log upload
            try:
                if self._audit_service:
                    self._audit_service.log(ActivityLogCreateDTO(
                        action=getattr(Variables, "MEDIA_UPLOADED", "media_uploaded"),
                        user_id=owner_id if owner_type == AssetOwnerType.USER else "system",
                        entity_type=getattr(Variables, "MEDIA_ENTITY_TYPE", "MediaAsset"),
                        entity_id=str(asset.id),
                        after=MediaAssetResponseDTO.from_model(asset),
                        created_by=owner_id if owner_type == AssetOwnerType.USER else "system",
                        ip_address="system",
                        user_agent="system"
                    ))
            except Exception as audit_exc:
                logger.error("[MediaService.upload_file] Audit logging failed: %r", audit_exc)

            return MediaAssetResponseDTO.from_model(asset)
        except Exception as exc:
            if os.path.exists(absolute_file_path):
                try:
                    os.remove(absolute_file_path)
                except Exception as cleanup_exc:
                    logger.error("[MediaService.upload_file] File cleanup failed: %r", cleanup_exc)
            logger.error("[MediaService.upload_file] Failed: %r", exc)
            raise exc

    def get_by_id(self, asset_id: str) -> MediaAssetResponseDTO:
        asset = self._repo.get_by_id(asset_id)
        if not asset:
            raise NotFound("MediaAsset not found")
        return MediaAssetResponseDTO.from_model(asset)

    def verify_download_permission(self, asset_id: str, user_id: str) -> bool:
        user = self._repos.user.get_user_by_id(user_id)

        asset = self._repo.get_by_id(asset_id)
        if not asset:
            return False
        if user.is_admin:
            return True
        if asset.is_public:
            return True

        if asset.owner_type == AssetOwnerType.USER:
            return str(asset.owner_id) == str(user.id)

        elif asset.owner_type == AssetOwnerType.ORDER:
            order = self._repos.order.get_by_id(str(asset.owner_id))
            if order and str(order.client_id) == str(user.id):
                return True

        elif asset.owner_type == AssetOwnerType.DELIVERY:
            delivery = self._repos.order_delivery.get_by_id(str(asset.owner_id))
            if delivery:
                order = self._repos.order.get_by_id(str(delivery.order_id))
                if order and str(order.client_id) == str(user.id):
                    return True
        return False

    def create_bulk_zip(self, asset_ids: List[str], user_id: str) -> str:
        user = self._repos.user.get_user_by_id(user_id)
        allowed_assets: List[MediaAsset] = []
        for aid in asset_ids:
            asset = self._repo.get_by_id(aid)
            if asset and self.verify_download_permission(str(asset.id), str(user.id)):
                allowed_assets.append(asset)

        if not allowed_assets:
            raise ValidationError("No authorized or valid files selected for download")

        upload_root = current_app.config.get("UPLOAD_ROOT", "/home/vault/tunedBundle/uploads")
        temp_dir = os.path.join(upload_root, "temp")
        os.makedirs(temp_dir, exist_ok=True)

        zip_filename = f"{uuid.uuid4()}.zip"
        zip_path = os.path.join(temp_dir, zip_filename)

        try:
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for asset in allowed_assets:
                    physical_path = os.path.join(upload_root, asset.storage_path)
                    if os.path.exists(physical_path):
                        # Use original filename inside zip
                        zip_file.write(physical_path, asset.original_filename)

            # Log download
            try:
                if self._audit_service:
                    self._audit_service.log(ActivityLogCreateDTO(
                        action="media_bulk_download",
                        user_id=str(user.id),
                        entity_type="MediaAsset",
                        entity_id=zip_filename,
                        before=None,
                        after={"count": len(allowed_assets)},
                        created_by=str(user.id),
                        ip_address="system",
                        user_agent="system"
                    ))
            except Exception as audit_exc:
                logger.error("[MediaService.create_bulk_zip] Audit logging failed: %r", audit_exc)

            return f"temp/{zip_filename}"
        except Exception as exc:
            if os.path.exists(zip_path):
                os.remove(zip_path)
            logger.error("[MediaService.create_bulk_zip] Zip creation failed: %r", exc)
            raise ServiceError("Failed to create download package") from exc

    def create_order_zip(self, order_id: str, user_id: str) -> str:
        user = self._repos.user.get_user_by_id(user_id)
        order = self._repos.order.get_by_id(order_id)
        if not order:
            raise NotFound("Order not found")

        # Permission check
        if not user.is_admin and str(order.client_id) != str(user.id):
            raise ValidationError("You are not authorized to access files for this order")

        # Collect order requirement files
        asset_ids = []
        for f in order.files:
            if f.asset_id:
                asset_ids.append(str(f.asset_id))

        if not asset_ids:
            raise NotFound("No files uploaded for this order")

        return self.create_bulk_zip(asset_ids, user_id)

    def create_delivery_zip(self, delivery_id: str, user_id: str) -> str:
        user = self._repos.user.get_user_by_id(user_id)
        delivery = self._repos.order_delivery.get_by_id(delivery_id)
        if not delivery:
            raise NotFound("Delivery not found")

        order = self._repos.order.get_by_id(str(delivery.order_id))
        if not order:
            raise NotFound("Order for delivery not found")

        # Permission check
        if not user.is_admin and str(order.client_id) != str(user.id):
            raise ValidationError("You are not authorized to access files for this delivery")

        asset_ids = []
        for f in delivery.delivery_files:
            if f.asset_id:
                asset_ids.append(str(f.asset_id))

        if not asset_ids:
            raise NotFound("No files uploaded for this delivery")

        return self.create_bulk_zip(asset_ids, user_id)

    def delete_media(self, asset_id: str) -> None:
        self._repo.delete(asset_id)
