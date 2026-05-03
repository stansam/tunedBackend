from sqlalchemy.orm import Session
from sqlalchemy import select
from tuned.models.payment import AcceptedPaymentMethod
from tuned.models.enums import MethodCategory
from tuned.dtos.payment import AcceptedMethodCreateDTO, AcceptedMethodUpdateDTO, AcceptedMethodResponseDTO
from tuned.repository.exceptions import NotFound, DatabaseError

class AcceptedPaymentMethodRepository:
    def __init__(self, session: Session):
        self._session = session

    def create(self, data: AcceptedMethodCreateDTO) -> AcceptedMethodResponseDTO:
        try:
            method = AcceptedPaymentMethod(
                name=data.name,
                category=MethodCategory(data.category.lower()) if isinstance(data.category, str) else data.category,
                details=data.details,
                is_active=data.is_active if data.is_active is not None else True
            )
            self._session.add(method)
            self._session.flush()
            return AcceptedMethodResponseDTO.from_model(method)
        except Exception as e:
            raise DatabaseError(f"Failed to create accepted payment method: {str(e)}") from e

    def update(self, method_id: str, data: AcceptedMethodUpdateDTO) -> AcceptedMethodResponseDTO:
        try:
            stmt = select(AcceptedPaymentMethod).where(AcceptedPaymentMethod.id == method_id)
            method = self._session.scalar(stmt)
            if not method:
                raise NotFound(f"Accepted method {method_id} not found")
            
            if data.name is not None:
                method.name = data.name
            if data.category is not None:
                method.category = MethodCategory(data.category.lower()) if isinstance(data.category, str) else data.category
            if data.details is not None:
                method.details = data.details
            if data.is_active is not None:
                method.is_active = data.is_active
                
            self._session.flush()
            return AcceptedMethodResponseDTO.from_model(method)
        except NotFound:
            raise
        except Exception as e:
            raise DatabaseError(f"Failed to update accepted payment method: {str(e)}") from e

    def get_by_id(self, method_id: str) -> AcceptedMethodResponseDTO:
        stmt = select(AcceptedPaymentMethod).where(AcceptedPaymentMethod.id == method_id)
        method = self._session.scalar(stmt)
        if not method:
            raise NotFound(f"Accepted method {method_id} not found")
        return AcceptedMethodResponseDTO.from_model(method)

    def get_all_active(self) -> list[AcceptedMethodResponseDTO]:
        stmt = select(AcceptedPaymentMethod).where(AcceptedPaymentMethod.is_active == True)
        methods = self._session.scalars(stmt).all()
        return [AcceptedMethodResponseDTO.from_model(m) for m in methods]
