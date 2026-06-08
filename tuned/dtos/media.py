from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from tuned.dtos.base import BaseDTO
from tuned.models.enums import FileExtensionType, AssetOwnerType

if TYPE_CHECKING:
    from tuned.models.media import MediaAsset


@dataclass(kw_only=True)
class MediaAssetCreateDTO:
    original_filename: str
    storage_path: str
    asset_type: FileExtensionType
    file_size_bytes: Optional[int] = None
    width_px: Optional[int] = None
    height_px: Optional[int] = None
    alt_text: Optional[str] = None
    is_public: bool = True
    checksum_sha256: Optional[str] = None
    owner_type: Optional[AssetOwnerType] = None
    owner_id: Optional[str] = None


@dataclass(kw_only=True)
class MediaAssetResponseDTO(BaseDTO):
    id: str
    original_filename: str
    storage_path: str
    asset_type: FileExtensionType
    file_size_bytes: Optional[int]
    width_px: Optional[int]
    height_px: Optional[int]
    alt_text: Optional[str]
    is_public: bool
    checksum_sha256: Optional[str]
    owner_type: Optional[AssetOwnerType]
    owner_id: Optional[str]

    @classmethod
    def from_model(cls, model: "MediaAsset") -> "MediaAssetResponseDTO":
        return cls(
            id=str(model.id),
            original_filename=model.original_filename,
            storage_path=model.storage_path,
            asset_type=model.asset_type,
            file_size_bytes=model.file_size_bytes,
            width_px=model.width_px,
            height_px=model.height_px,
            alt_text=model.alt_text,
            is_public=model.is_public,
            checksum_sha256=model.checksum_sha256,
            owner_type=model.owner_type,
            owner_id=str(model.owner_id) if model.owner_id else None,
            created_at=model.created_at,
            updated_at=model.updated_at,
            is_deleted=getattr(model, "is_deleted", False)
        )
