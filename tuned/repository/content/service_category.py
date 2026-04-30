from sqlalchemy.orm import Session
from typing import Any
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from tuned.models.service import ServiceCategory
from tuned.dtos.services import ServiceCategoryDTO, ServiceCategoryResponseDTO, ServiceCategoryUpdateDTO
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound

class CreateServiceCategory:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, data: ServiceCategoryDTO) -> ServiceCategoryResponseDTO:
        try:
            category = ServiceCategory(
                name=data.name,
                description=data.description,
                order=data.order,
            )
            self.session.add(category)
            self.session.flush()
            return ServiceCategoryResponseDTO.from_model(category)
        except IntegrityError:
            raise AlreadyExists("A service category with this name already exists.")
        except SQLAlchemyError as e:
            raise DatabaseError("Database error while creating service category.") from e

class GetServiceCategoryByID:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, category_id: str) -> ServiceCategoryResponseDTO:
        try:
            stmt = select(ServiceCategory).where(ServiceCategory.id == category_id)
            category = self.session.scalar(stmt)
            if not category:
                raise NotFound("Service category not found.")
            return ServiceCategoryResponseDTO.from_model(category)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching service category: {str(e)}") from e

class GetAllServiceCategories:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self) -> list[ServiceCategoryResponseDTO]:
        try:
            stmt = select(ServiceCategory).order_by(ServiceCategory.order.asc())
            categories = self.session.scalars(stmt).all()
            return [ServiceCategoryResponseDTO.from_model(category) for category in categories]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching service categories: {str(e)}") from e

class UpdateServiceCategory:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, category_id: str, updates: ServiceCategoryUpdateDTO) -> ServiceCategoryResponseDTO:
        try:
            stmt = select(ServiceCategory).where(ServiceCategory.id == category_id)
            category = self.session.scalar(stmt)
            if not category:
                raise NotFound("Service category not found.")
            update_data = {k: v for k, v in updates.__dict__.items() if v is not None}
            for key, value in update_data.items():
                if hasattr(category, key):
                    setattr(category, key, value)
            self.session.flush()
            return ServiceCategoryResponseDTO.from_model(category)
        except IntegrityError:
            raise AlreadyExists("A service category with that name already exists.")
        except SQLAlchemyError as e:
            raise DatabaseError("Database error while updating service category.") from e

class DeleteServiceCategory:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, category_id: str) -> None:
        try:
            stmt = select(ServiceCategory).where(ServiceCategory.id == category_id)
            category = self.session.scalar(stmt)
            if not category:
                raise NotFound("Service category not found.")
            self.session.delete(category)
            self.session.flush()
        except SQLAlchemyError as e:
            raise DatabaseError("Database error while deleting service category.") from e

from tuned.repository.protocols import ServiceCategoryRepositoryProtocol

class ServiceCategoryRepository(ServiceCategoryRepositoryProtocol):
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, data: ServiceCategoryDTO) -> ServiceCategoryResponseDTO:
        return CreateServiceCategory(self.session).execute(data)

    def get_by_id(self, category_id: str) -> ServiceCategoryResponseDTO:
        return GetServiceCategoryByID(self.session).execute(category_id)

    def get_all(self) -> list[ServiceCategoryResponseDTO]:
        return GetAllServiceCategories(self.session).execute()

    def update(self, category_id: str, updates: ServiceCategoryUpdateDTO) -> ServiceCategoryResponseDTO:
        return UpdateServiceCategory(self.session).execute(category_id, updates)

    def delete(self, category_id: str) -> None:
        return DeleteServiceCategory(self.session).execute(category_id)
