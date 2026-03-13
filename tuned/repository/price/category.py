from tuned.models import PricingCategory
from sqlalchemy.exc import Session
from tuned.dtos import PricingCategoryDTO
from tuned.repository.exceptions import AlreadyExists, DatabaseError

class PricingCategoryRepo:
    def __init__(self, db:Session):
        self.db = db
    def Create(self, data: PricingCategoryDTO) -> PricingCategory:
        try:
            category = PricingCategory(**data)

            self.db.session.add(category)
            self.db.session.commit()
        except IntegrityError as e:
            self.db.rollback()
            raise AlreadyExists("pricing category already exists")
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError("Database error while creating pricing category") from e

