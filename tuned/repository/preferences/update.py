from sqlalchemy.orm import Session
from tuned.repository.exceptions import DatabaseError
from sqlalchemy.exc import SQLAlchemyError
from tuned.models.enums import (
    EmailFrequency, ProfileVisibility, DateFormat, TimeFormat, NumberFormat, WeekStart, InvoiceDeliveryMethod
)

from typing import Any

class UpdatePreferenceCategory:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, model: type[Any], user_id: str, data: dict[str, Any]) -> Any: #TODO: Implement strict typing for this function
        try:
            obj = self.session.query(model).filter_by(user_id=user_id).first()
            if not obj:
                obj = model(user_id=user_id)
                self.session.add(obj)
            
            enum_mappings = {
                'frequency': EmailFrequency,
                'profile_visibility': ProfileVisibility,
                'date_format': DateFormat,
                'time_format': TimeFormat,
                'number_format': NumberFormat,
                'week_start': WeekStart,
                'invoice_delivery': InvoiceDeliveryMethod
            }

            for key, value in data.items():
                if hasattr(obj, key):
                    if key in enum_mappings and isinstance(value, str):
                        try:
                            setattr(obj, key, enum_mappings[key](value))
                        except ValueError:
                            pass
                    else:
                        setattr(obj, key, value)
            
            self.session.flush()
            return obj
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while updating preference category: {str(e)}")
