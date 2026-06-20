from typing import TYPE_CHECKING, Any
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tuned.models.base import BaseModel
from tuned.models.enums import FileExtensionType, AssetOwnerType
from tuned.extensions import db

if TYPE_CHECKING:
    from tuned.models.order import OrderFile
    from tuned.models.order_delivery import OrderDeliveryFile


class MediaAsset(BaseModel):  # type: ignore[name-defined, misc]
    """
    A single uploaded file, owned by one domain entity.

    Columns
    -------
    original_filename   Name the user uploaded (sanitised before storing).
    storage_path        Relative path of the file.
    asset_type          MIME-type enum — drives validation and rendering.
    file_size_bytes     Used for storage quota tracking.
    width_px / height_px Populated for image assets after processing.
    alt_text            Accessibility alt text for images.
    is_public           False for receipts / sensitive documents.
    owner_type          Which model owns this asset.
    owner_id            PK of the owning record (polymorphic, not a real FK).
    checksum_sha256     File integrity hash; verified on upload.
    """

    __tablename__ = "media_assets"

    # File identity
    original_filename: Mapped[str] = mapped_column(db.String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(
        db.String(500), nullable=False, unique=True,
        doc="relative path of the file.",
    )

    asset_type: Mapped[FileExtensionType] = mapped_column(
        db.Enum(FileExtensionType, name="file_extension_type_enum"),
        nullable=False,
        index=True,
    )
    file_size_bytes: Mapped[int | None] = mapped_column(db.BigInteger, nullable=True)
    width_px: Mapped[int | None] = mapped_column(db.Integer, nullable=True)
    height_px: Mapped[int | None] = mapped_column(db.Integer, nullable=True)
    alt_text: Mapped[str | None] = mapped_column(
        db.String(500), nullable=True,
        doc="Screen-reader accessible description for image assets.",
    )
    is_public: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, default=True,
        doc="False for receipts and sensitive documents; signed URLs only.",
    )
    checksum_sha256: Mapped[str | None] = mapped_column(
        db.String(64), nullable=True,
        doc="SHA-256 hex digest verified on upload.",
    )

    # Polymorphic ownership
    owner_type: Mapped[AssetOwnerType | None] = mapped_column(
        ENUM(AssetOwnerType, name="asset_owner_type_enum"),
        nullable=True,
        index=True,
        doc="Which model owns this asset.",
    )
    owner_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True,
        doc="PK of the owning model row (not a real DB FK — polymorphic).",
    )

    order_files: Mapped[list["OrderFile"]] = relationship(
        "OrderFile",
        back_populates="asset",
        cascade="all, delete-orphan",
    )
    delivery_files: Mapped[list["OrderDeliveryFile"]] = relationship(
        "OrderDeliveryFile",
        back_populates="asset",
        cascade="all, delete-orphan",
    )

    def __init__(self, **kwargs: Any) -> None:
        super(MediaAsset, self).__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<MediaAsset {self.asset_type.value} {self.original_filename!r}>"
