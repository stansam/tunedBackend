from sqlalchemy.orm import Session
from tuned.repository.exceptions import DatabaseError
from sqlalchemy.exc import SQLAlchemyError
from tuned.models.enums import (
    EmailFrequency, ProfileVisibility, DateFormat, TimeFormat, NumberFormat, WeekStart, InvoiceDeliveryMethod
)

class UpdatePreferenceCategory:
    def __init__(self, db: Session):
        self.db = db

    def execute(self, model, user_id: str, data: dict):
        try:
            obj = self.db.query(model).filter_by(user_id=user_id).first()
            if not obj:
                obj = model(user_id=user_id)
                self.db.add(obj)
            
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
            
            self.db.flush()
            return obj
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while updating preference category: {str(e)}")
