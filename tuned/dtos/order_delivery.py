from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from tuned.models.enums import DeliveryStatus, FileType, FileExtensionType
from tuned.models.order_delivery import OrderDelivery, OrderDeliveryFile

@dataclass
class OrderDeliveryFileDTO:
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    file_type: FileType
    file_format: FileExtensionType
    description: Optional[str] = None
    
    def __post_init__(self):
        if isinstance(self.file_type, str):
            self.file_type = FileType(self.file_type)
        if isinstance(self.file_format, str):
            self.file_format = FileExtensionType(self.file_format)

@dataclass
class CreateOrderDeliveryDTO:
    order_id: str
    delivery_files: list[OrderDeliveryFileDTO] = field(default_factory=list)

@dataclass
class AddDeliveryFilesDTO:
    delivery_files: list[OrderDeliveryFileDTO] = field(default_factory=list)

@dataclass
class OrderDeliveryFileResponseDTO:
    id: str
    delivery_id: str
    filename: str
    original_filename: str
    file_path: str
    file_type: str
    file_format: str
    description: Optional[str]
    file_size: int
    is_plagiarism_report: bool
    file_icon: str
    created_at: str

    @classmethod
    def from_model(cls, model: OrderDeliveryFile) -> "OrderDeliveryFileResponseDTO":
        return cls(
            id=str(model.id),
            delivery_id=str(model.delivery_id),
            filename=model.filename,
            original_filename=model.original_filename,
            file_path=model.file_path,
            file_type=model.file_type.value if hasattr(model.file_type, 'value') else model.file_type,
            file_format=model.file_format.value if hasattr(model.file_format, 'value') else model.file_format,
            description=model.description,
            file_size=model.file_size,
            is_plagiarism_report=model.is_plagiarism_report,
            file_icon=model.file_icon,
            created_at=model.created_at.isoformat() if model.created_at else "",
        )

@dataclass
class OrderDeliveryResponseDTO:
    id: str
    order_id: str
    delivery_status: str
    status_color: str
    client_notified: bool
    client_notified_at: Optional[str]
    has_plagiarism_report: bool
    delivery_files_count: int
    files: list[OrderDeliveryFileResponseDTO]
    created_at: str

    @classmethod
    def from_model(cls, model: OrderDelivery) -> "OrderDeliveryResponseDTO":
        return cls(
            id=str(model.id),
            order_id=str(model.order_id),
            delivery_status=model.delivery_status.value if hasattr(model.delivery_status, 'value') else model.delivery_status,
            status_color=model.status_color,
            client_notified=model.client_notified,
            client_notified_at=model.client_notified_at.isoformat() if model.client_notified_at else None,
            has_plagiarism_report=model.has_plagiarism_report,
            delivery_files_count=model.delivery_files_count,
            files=[OrderDeliveryFileResponseDTO.from_model(f) for f in model.delivery_files],
            created_at=model.created_at.isoformat() if model.created_at else "",
        )

@dataclass
class UpdateOrderDeliveryStatusDTO:
    delivery_status: DeliveryStatus

    def __post_init__(self):
        if isinstance(self.delivery_status, str):
            self.delivery_status = DeliveryStatus(self.delivery_status)
