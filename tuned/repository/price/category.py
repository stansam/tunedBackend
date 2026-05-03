from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from tuned.models import PricingCategory
from tuned.dtos.price import PricingCategoryDTO, PricingCategoryResponseDTO, PricingCategoryUpdateDTO
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound


class CreatePricingCategory:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, data: PricingCategoryDTO) -> PricingCategoryResponseDTO:
        try:
            category = PricingCategory(
                name=data.name,
                description=data.description,
                display_order=data.display_order,
            )
            self.session.add(category)
            self.session.flush()
            return PricingCategoryResponseDTO.from_model(category)
        except IntegrityError:
            raise AlreadyExists("A pricing category with this name already exists.")
        except SQLAlchemyError as e:
            raise DatabaseError("Database error while creating pricing category.") from e


class GetPricingCategoryByID:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, category_id: str) -> PricingCategoryResponseDTO:
        try:
            stmt = select(PricingCategory).where(PricingCategory.id == category_id)
            category = self.session.scalar(stmt)
            if not category:
                raise NotFound("Pricing category not found.")
            return PricingCategoryResponseDTO.from_model(category)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching pricing category: {str(e)}") from e


class GetAllPricingCategories:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self) -> list[PricingCategoryResponseDTO]:
        try:
            stmt = select(PricingCategory).order_by(PricingCategory.display_order.asc())
            categories = self.session.scalars(stmt).all()
            return [PricingCategoryResponseDTO.from_model(c) for c in categories]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching pricing categories: {str(e)}") from e


class UpdatePricingCategory:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, category_id: str, updates: PricingCategoryUpdateDTO) -> PricingCategoryResponseDTO:
        try:
            stmt = select(PricingCategory).where(PricingCategory.id == category_id)
            category = self.session.scalar(stmt)
            if not category:
                raise NotFound("Pricing category not found.")
            update_data = {k: v for k, v in updates.__dict__.items() if v is not None}
            for key, value in update_data.items():
                if hasattr(category, key):
                    setattr(category, key, value)
            self.session.flush()
            return PricingCategoryResponseDTO.from_model(category)
        except IntegrityError:
            raise AlreadyExists("A pricing category with that name already exists.")
        except SQLAlchemyError as e:
            raise DatabaseError("Database error while updating pricing category.") from e


class DeletePricingCategory:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, category_id: str) -> None:
        try:
            stmt = select(PricingCategory).where(PricingCategory.id == category_id)
            category = self.session.scalar(stmt)
            if not category:
                raise NotFound("Pricing category not found.")
            self.session.delete(category)
            self.session.flush()
        except SQLAlchemyError as e:
            raise DatabaseError("Database error while deleting pricing category.") from e


from tuned.repository.protocols import PricingCategoryRepositoryProtocol

class PricingCategoryRepository(PricingCategoryRepositoryProtocol):
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, data: PricingCategoryDTO) -> PricingCategoryResponseDTO:
        return CreatePricingCategory(self.session).execute(data)

    def get_by_id(self, category_id: str) -> PricingCategoryResponseDTO:
        return GetPricingCategoryByID(self.session).execute(category_id)

    def get_all(self) -> list[PricingCategoryResponseDTO]:
        return GetAllPricingCategories(self.session).execute()

    def update(self, category_id: str, updates: PricingCategoryUpdateDTO) -> PricingCategoryResponseDTO:
        return UpdatePricingCategory(self.session).execute(category_id, updates)

    def delete(self, category_id: str) -> None:
        return DeletePricingCategory(self.session).execute(category_id)
