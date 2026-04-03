from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from tuned.extensions import db
from tuned.models.service import ServiceCategory
from tuned.dtos.services import ServiceCategoryDTO, ServiceCategoryResponseDTO
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound

class CreateServiceCategory:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, data: ServiceCategoryDTO) -> ServiceCategoryResponseDTO:
        try:
            category = ServiceCategory(
                name=data.name,
                description=data.description,
                order=data.order,
            )
            self.db.session.add(category)
            self.db.session.commit()
            return ServiceCategoryResponseDTO.from_model(category)
        except IntegrityError:
            self.db.session.rollback()
            raise AlreadyExists("A service category with this name already exists.")
        except SQLAlchemyError as e:
            self.db.session.rollback()
            raise DatabaseError("Database error while creating service category.") from e

class GetServiceCategoryByID:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, category_id: str) -> ServiceCategoryResponseDTO:
        try:
            category = self.db.session.query(ServiceCategory).filter_by(id=category_id).first()
            if not category:
                raise NotFound("Service category not found.")
            return ServiceCategoryResponseDTO.from_model(category)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching service category: {str(e)}") from e

class GetAllServiceCategories:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self) -> list[ServiceCategoryResponseDTO]:
        try:
            categories = (
                self.db.session.query(ServiceCategory)
                .order_by(ServiceCategory.order.asc())
                .all()
            )
            return [ServiceCategoryResponseDTO.from_model(category) for category in categories]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching service categories: {str(e)}") from e

class UpdateServiceCategory:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, category_id: str, updates: dict) -> ServiceCategoryResponseDTO:
        try:
            category = self.db.session.query(ServiceCategory).filter_by(id=category_id).first()
            if not category:
                raise NotFound("Service category not found.")
            for key, value in updates.items():
                if hasattr(category, key):
                    setattr(category, key, value)
            self.db.session.commit()
            return ServiceCategoryResponseDTO.from_model(category)
        except IntegrityError:
            self.db.session.rollback()
            raise AlreadyExists("A service category with that name already exists.")
        except SQLAlchemyError as e:
            self.db.session.rollback()
            raise DatabaseError("Database error while updating service category.") from e

class DeleteServiceCategory:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, category_id: str) -> None:
        try:
            category = self.db.session.query(ServiceCategory).filter_by(id=category_id).first()
            if not category:
                raise NotFound("Service category not found.")
            self.db.session.delete(category)
            self.db.session.commit()
        except SQLAlchemyError as e:
            self.db.session.rollback()
            raise DatabaseError("Database error while deleting service category.") from e

class ServiceCategoryRepository:
    def __init__(self) -> None:
        self.db = db

    def create(self, data: ServiceCategoryDTO) -> ServiceCategoryResponseDTO:
        return CreateServiceCategory(self.db).execute(data)

    def get_by_id(self, category_id: str) -> ServiceCategoryResponseDTO:
        return GetServiceCategoryByID(self.db).execute(category_id)

    def get_all(self) -> list[ServiceCategoryResponseDTO]:
        return GetAllServiceCategories(self.db).execute()

    def update(self, category_id: str, updates: dict) -> ServiceCategoryResponseDTO:
        return UpdateServiceCategory(self.db).execute(category_id, updates)

    def delete(self, category_id: str) -> None:
        return DeleteServiceCategory(self.db).execute(category_id)
