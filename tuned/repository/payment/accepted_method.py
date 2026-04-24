from sqlalchemy.orm import Session
from tuned.models.payment import AcceptedPaymentMethod
from tuned.dtos.payment import AcceptedMethodCreateDTO, AcceptedMethodUpdateDTO, AcceptedMethodResponseDTO
from tuned.core.exceptions import NotFound, DatabaseError

class AcceptedPaymentMethodRepository:
    def __init__(self, db:Session ):
        self._db = db

    def create(self, data: AcceptedMethodCreateDTO) -> AcceptedMethodResponseDTO:
        try:
            method = AcceptedPaymentMethod(
                name=data.name,
                category=data.category,
                details=data.details,
                is_active=data.is_active
            )
            self._db.add(method)
            self._db.commit()
            return AcceptedMethodResponseDTO.from_model(method)
        except Exception as e:
            self._db.rollback()
            raise DatabaseError(f"Failed to create accepted payment method: {str(e)}")

    def update(self, method_id: str, data: AcceptedMethodUpdateDTO) -> AcceptedMethodResponseDTO:
        try:
            method = AcceptedPaymentMethod.query.get(method_id)
            if not method:
                raise NotFound(f"Accepted method {method_id} not found")
            
            if data.name is not None:
                method.name = data.name
            if data.category is not None:
                method.category = data.category
            if data.details is not None:
                method.details = data.details
            if data.is_active is not None:
                method.is_active = data.is_active
                
            self._db.commit()
            return AcceptedMethodResponseDTO.from_model(method)
        except NotFound:
            raise
        except Exception as e:
            self._db.rollback()
            raise DatabaseError(f"Failed to update accepted payment method: {str(e)}")

    def get_by_id(self, method_id: str) -> AcceptedMethodResponseDTO:
        method = AcceptedPaymentMethod.query.get(method_id)
        if not method:
            raise NotFound(f"Accepted method {method_id} not found")
        return AcceptedMethodResponseDTO.from_model(method)

    def get_all_active(self) -> list[AcceptedMethodResponseDTO]:
        methods = AcceptedPaymentMethod.query.filter_by(is_active=True).all()
        return [AcceptedMethodResponseDTO.from_model(m) for m in methods]
