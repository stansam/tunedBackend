from tuned.models import PriceRate, PricingCategory
from sqlalchemy.exc import Session
from tuned.dtos import PriceRateDTO, PricingCategoryDTO
from tuned.repository.exceptions import AlreadyExists, DatabaseError

class PriceRateRepo:
    def __init__(self, db:Session):
        self.db = db
    def Create(self, data: PriceRateDTO) -> PriceRate:
        try:
            rate = PriceRate(**data)

            self.db.session.add(rate)
            self.db.session.commit()
        except IntegrityError as e:
            self.db.rollback()
            raise AlreadyExists("price rate already exists")
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError("Database error while creating price rate") from e

