from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
from tuned.models.media import MediaAsset
from tuned.dtos.media import MediaAssetCreateDTO
from tuned.repository.exceptions import DatabaseError, NotFound
from tuned.repository.protocols.media import MediaRepositoryProtocol
from typing import Optional
import uuid

class MediaRepository(MediaRepositoryProtocol):
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, data: MediaAssetCreateDTO) -> MediaAsset:
        try:
            asset = MediaAsset(
                original_filename=data.original_filename,
                storage_path=data.storage_path,
                asset_type=data.asset_type,
                file_size_bytes=data.file_size_bytes,
                width_px=data.width_px,
                height_px=data.height_px,
                alt_text=data.alt_text,
                is_public=data.is_public,
                checksum_sha256=data.checksum_sha256,
                owner_type=data.owner_type,
                owner_id=uuid.UUID(data.owner_id) if data.owner_id else None
            )
            self.session.add(asset)
            self.session.flush()
            return asset
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while registering media: {str(e)}") from e

    def get_by_id(self, asset_id: str) -> Optional[MediaAsset]:
        try:
            stmt = select(MediaAsset).where(
                MediaAsset.id == uuid.UUID(asset_id),
                MediaAsset.is_deleted == False
            )
            return self.session.scalar(stmt)
        except ValueError:
            return None
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching media: {str(e)}") from e

    def get_by_storage_path(self, storage_path: str) -> Optional[MediaAsset]:
        try:
            stmt = select(MediaAsset).where(
                MediaAsset.storage_path == storage_path,
                MediaAsset.is_deleted == False
            )
            return self.session.scalar(stmt)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching media path: {str(e)}") from e

    def delete(self, asset_id: str) -> None:
        try:
            stmt = select(MediaAsset).where(
                MediaAsset.id == uuid.UUID(asset_id),
                MediaAsset.is_deleted == False
            )
            asset = self.session.scalar(stmt)
            if not asset:
                raise NotFound(f"MediaAsset {asset_id} not found")
            asset.is_deleted = True
            asset.deleted_at = datetime.now(timezone.utc)
            self.session.flush()
        except NotFound:
            raise
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while deleting media: {str(e)}") from e

    def save(self) -> None:
        try:
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f"Database error while saving changes: {str(e)}") from e

    def rollback(self) -> None:
        self.session.rollback()
