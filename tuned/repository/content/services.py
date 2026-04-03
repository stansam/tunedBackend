from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from tuned.extensions import db
from tuned.models import Service
from tuned.dtos.services import ServiceDTO, ServiceResponseDTO
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound

class CreateService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, data: ServiceDTO) -> ServiceResponseDTO:
        try:
            service = Service(
                name=data.name,
                description=data.description,
                category_id=data.category_id,
                featured=data.featured,
                pricing_category_id=data.pricing_category_id,
                slug=data.slug or None,
                is_active=data.is_active if data.is_active is not None else True,
            )
            self.db.session.add(service)
            self.db.session.commit()
            return ServiceResponseDTO.from_model(service)
        except IntegrityError:
            self.db.session.rollback()
            raise AlreadyExists("A service with this name or slug already exists.")
        except SQLAlchemyError as e:
            self.db.session.rollback()
            raise DatabaseError("Database error while creating service.") from e

class GetServiceByID:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, service_id: str) -> ServiceResponseDTO:
        try:
            service = self.db.session.query(Service).filter_by(id=service_id).first()
            if not service:
                raise NotFound("Service not found.")
            return ServiceResponseDTO.from_model(service)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching service: {str(e)}") from e

class GetServiceBySlug:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, slug: str) -> ServiceResponseDTO:
        try:
            service = self.db.session.query(Service).filter_by(slug=slug).first()
            if not service:
                raise NotFound("Service not found.")
            return ServiceResponseDTO.from_model(service)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching service: {str(e)}") from e

class GetAllServices:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, active_only: bool = True) -> list[ServiceResponseDTO]:
        try:
            query = self.db.session.query(Service)
            if active_only:
                query = query.filter_by(is_active=True)
            return [ServiceResponseDTO.from_model(service) for service in query.order_by(Service.name.asc()).all()]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching services: {str(e)}") from e

class GetFeaturedServices:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self) -> list[ServiceResponseDTO]:
        try:
            services = (
                self.db.session.query(Service)
                .filter_by(featured=True, is_active=True)
                .order_by(Service.name.asc())
                .all()
            )
            return [ServiceResponseDTO.from_model(service) for service in services]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching featured services: {str(e)}") from e

class UpdateService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, service_id: str, updates: dict) -> ServiceResponseDTO:
        try:
            service = self.db.session.query(Service).filter_by(id=service_id).first()
            if not service:
                raise NotFound("Service not found.")
            for key, value in updates.items():
                if hasattr(service, key):
                    setattr(service, key, value)
            self.db.session.commit()
            return ServiceResponseDTO.from_model(service)
        except IntegrityError:
            self.db.session.rollback()
            raise AlreadyExists("A service with that name or slug already exists.")
        except SQLAlchemyError as e:
            self.db.session.rollback()
            raise DatabaseError("Database error while updating service.") from e

class DeleteService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, service_id: str) -> None:
        try:
            service = self.db.session.query(Service).filter_by(id=service_id).first()
            if not service:
                raise NotFound("Service not found.")
            self.db.session.delete(service)
            self.db.session.commit()
        except SQLAlchemyError as e:
            self.db.session.rollback()
            raise DatabaseError("Database error while deleting service.") from e
    
class GetServicesByCategory:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, category_id: str) -> list[ServiceResponseDTO]:
        try:
            services = self.db.session.query(Service).filter_by(category_id=category_id).all()
            if not services:
                raise NotFound("No services found in this category.")
            return [ServiceResponseDTO.from_model(service) for service in services]
        except SQLAlchemyError as e:
            raise DatabaseError("Database error while fetching services by category.") from e


class ServiceRepository:
    def __init__(self) -> None:
        self.db = db

    def create(self, data: ServiceDTO) -> ServiceResponseDTO:
        return CreateService(self.db).execute(data)

    def get_by_id(self, service_id: str) -> ServiceResponseDTO:
        return GetServiceByID(self.db).execute(service_id)

    def get_by_slug(self, slug: str) -> ServiceResponseDTO:
        return GetServiceBySlug(self.db).execute(slug)

    def get_all(self, active_only: bool = True) -> list[ServiceResponseDTO]:
        return GetAllServices(self.db).execute(active_only)

    def get_featured(self) -> list[ServiceResponseDTO]:
        return GetFeaturedServices(self.db).execute()

    def update(self, service_id: str, updates: dict) -> ServiceResponseDTO:
        return UpdateService(self.db).execute(service_id, updates)

    def delete(self, service_id: str) -> None:
        return DeleteService(self.db).execute(service_id)
    def get_services_by_category(self, category_id: str) -> list[ServiceResponseDTO]:
        return GetServicesByCategory(self.db).execute(category_id)