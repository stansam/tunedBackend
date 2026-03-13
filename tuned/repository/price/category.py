from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from tuned.extensions import db
from tuned.models import PricingCategory
from tuned.dtos.price import PricingCategoryDTO, PricingCategoryResponseDTO
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound


class CreatePricingCategory:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, data: PricingCategoryDTO) -> PricingCategoryResponseDTO:
        try:
            category = PricingCategory(
                name=data.name,
                description=data.description,
                display_order=data.display_order,
            )
            self.db.session.add(category)
            self.db.session.commit()
            return PricingCategoryResponseDTO.from_model(category)
        except IntegrityError:
            self.db.session.rollback()
            raise AlreadyExists("A pricing category with this name already exists.")
        except SQLAlchemyError as e:
            self.db.session.rollback()
            raise DatabaseError("Database error while creating pricing category.") from e


class GetPricingCategoryByID:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, category_id: str) -> PricingCategoryResponseDTO:
        try:
            category = self.db.session.query(PricingCategory).filter_by(id=category_id).first()
            if not category:
                raise NotFound("Pricing category not found.")
            return PricingCategoryResponseDTO.from_model(category)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching pricing category: {str(e)}") from e


class GetAllPricingCategories:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self) -> list[PricingCategoryResponseDTO]:
        try:
            categories = (
                self.db.session.query(PricingCategory)
                .order_by(PricingCategory.display_order.asc())
                .all()
            )
            return [PricingCategoryResponseDTO.from_model(c) for c in categories]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching pricing categories: {str(e)}") from e


class UpdatePricingCategory:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, category_id: str, updates: dict) -> PricingCategoryResponseDTO:
        try:
            category = self.db.session.query(PricingCategory).filter_by(id=category_id).first()
            if not category:
                raise NotFound("Pricing category not found.")
            for key, value in updates.items():
                if hasattr(category, key):
                    setattr(category, key, value)
            self.db.session.commit()
            return PricingCategoryResponseDTO.from_model(category)
        except IntegrityError:
            self.db.session.rollback()
            raise AlreadyExists("A pricing category with that name already exists.")
        except SQLAlchemyError as e:
            self.db.session.rollback()
            raise DatabaseError("Database error while updating pricing category.") from e


class DeletePricingCategory:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, category_id: str) -> None:
        try:
            category = self.db.session.query(PricingCategory).filter_by(id=category_id).first()
            if not category:
                raise NotFound("Pricing category not found.")
            self.db.session.delete(category)
            self.db.session.commit()
        except SQLAlchemyError as e:
            self.db.session.rollback()
            raise DatabaseError("Database error while deleting pricing category.") from e


class PricingCategoryRepository:
    """Facade composing all PricingCategory command objects."""

    def __init__(self) -> None:
        self.db = db

    def create(self, data: PricingCategoryDTO) -> PricingCategoryResponseDTO:
        return CreatePricingCategory(self.db).execute(data)

    def get_by_id(self, category_id: str) -> PricingCategoryResponseDTO:
        return GetPricingCategoryByID(self.db).execute(category_id)

    def get_all(self) -> list[PricingCategoryResponseDTO]:
        return GetAllPricingCategories(self.db).execute()

    def update(self, category_id: str, updates: dict) -> PricingCategoryResponseDTO:
        return UpdatePricingCategory(self.db).execute(category_id, updates)

    def delete(self, category_id: str) -> None:
        return DeletePricingCategory(self.db).execute(category_id)
