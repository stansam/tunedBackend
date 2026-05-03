from datetime import datetime
from tuned.extensions import db
from tuned.models.enums import DeliveryStatus, FileType
from tuned.models.base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from tuned.models.order import Order
    from tuned.models.revision_request import OrderRevisionRequest

class OrderDelivery(BaseModel):
    __tablename__ = 'order_delivery'
    order_id: Mapped[str] = mapped_column(db.String(36), db.ForeignKey('order.id'), nullable=False)
    delivery_status: Mapped[DeliveryStatus] = mapped_column(db.Enum(DeliveryStatus), default=DeliveryStatus.DELIVERED, nullable=False)
    client_notified: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    client_notified_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
        
    delivery_files: Mapped[list["OrderDeliveryFile"]] = relationship('OrderDeliveryFile', back_populates='delivery', lazy=True, cascade="all, delete-orphan")
    order: Mapped[Optional["Order"]] = relationship('Order', back_populates='deliveries')
    revision_requests: Mapped[list["OrderRevisionRequest"]] = relationship('OrderRevisionRequest', back_populates='delivery', lazy='dynamic')
    
    __table_args__ = (
        db.Index('ix_delivery_order_date', 'order_id', 'created_at'),
    )
    
    @property
    def has_plagiarism_report(self) -> bool:
        return any(file.file_type == FileType.PLAGIARISM_REPORT for file in self.delivery_files)
    
    @property
    def delivery_files_count(self) -> int:
        return len([file for file in self.delivery_files if file.file_type == FileType.DELIVERY])
    
    @property
    def status_color(self) -> str:
        colors = {
            DeliveryStatus.DELIVERED: 'success',
            DeliveryStatus.REVISED: 'warning', 
            DeliveryStatus.REDELIVERED: 'info'
        }
        return colors.get(self.delivery_status, 'secondary')
    
    def __repr__(self) -> str:
        return f'<OrderDelivery Order:{self.order_id} Status:{self.delivery_status}>'


class OrderDeliveryFile(BaseModel):
    __tablename__ = 'order_delivery_file'
    delivery_id: Mapped[str] = mapped_column(db.String(36), db.ForeignKey('order_delivery.id'), nullable=False)
    filename: Mapped[str] = mapped_column(db.String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(db.String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(db.String(255), nullable=False)
    file_type: Mapped[FileType] = mapped_column(db.Enum(FileType), nullable=False)
    file_format: Mapped[Optional[str]] = mapped_column(db.String(10), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    
    delivery: Mapped["OrderDelivery"] = relationship('OrderDelivery', back_populates='delivery_files')

    @property
    def file_size(self) -> int:
        import os
        try:
            return os.path.getsize(self.file_path)
        except (OSError, TypeError):
            return 0
    
    @property
    def file_size_mb(self) -> float:
        size_bytes = self.file_size
        return round(size_bytes / (1024 * 1024), 2) if size_bytes > 0 else 0.0
    
    @property
    def is_plagiarism_report(self) -> bool:
        return self.file_type == FileType.PLAGIARISM_REPORT
    
    @property
    def file_icon(self) -> str:
        icons = {
            'pdf': 'fa-file-pdf',
            'docx': 'fa-file-word',
            'doc': 'fa-file-word',
            'txt': 'fa-file-text',
            'zip': 'fa-file-archive',
            'rar': 'fa-file-archive'
        }
        return icons.get(self.file_format, 'fa-file') if self.file_format else 'fa-file'
    
    def __repr__(self) -> str:
        return f'<OrderDeliveryFile {self.filename} Type:{self.file_type}>'