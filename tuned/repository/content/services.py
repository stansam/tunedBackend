import logging
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import func
from tuned.extensions import db
from tuned.models import Service, ServiceCategory, Order
from tuned.dtos.services import ServiceDTO, ServiceResponseDTO
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound
from tuned.core.logging import get_logger

logger: logging.Logger = get_logger(__name__)

class CreateService:
    def __init__(self, session: Session) -> None:
        self.session = session

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
            )  # type: ignore[no-untyped-call]
            self.session.add(service)
            self.session.commit()
            return ServiceResponseDTO.from_model(service)
        except IntegrityError:
            self.session.rollback()
            raise AlreadyExists("A service with this name or slug already exists.")
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError("Database error while creating service.") from e

class GetServiceByID:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, service_id: str) -> ServiceResponseDTO:
        try:
            service = self.session.query(Service).filter_by(id=service_id).first()
            if not service:
                raise NotFound("Service not found.")
            return ServiceResponseDTO.from_model(service)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching service: {str(e)}") from e

class GetServiceBySlug:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, slug: str) -> ServiceResponseDTO:
        try:
            service = self.session.query(Service).filter_by(slug=slug).first()
            if not service:
                raise NotFound("Service not found.")
            return ServiceResponseDTO.from_model(service)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching service: {str(e)}") from e

class GetAllServices:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, active_only: bool = True) -> list[ServiceResponseDTO]:
        try:
            query = self.session.query(Service)
            if active_only:
                query = query.filter_by(is_active=True)
            return [ServiceResponseDTO.from_model(service) for service in query.order_by(Service.name.asc()).all()]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching services: {str(e)}") from e

class GetFeaturedServices:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self) -> list[ServiceResponseDTO]:
        try:
            services = (
                self.session.query(Service)
                .filter_by(featured=True, is_active=True)
                .order_by(Service.name.asc())
                .all()
            )
            return [ServiceResponseDTO.from_model(service) for service in services]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching featured services: {str(e)}") from e

class UpdateService:
    def __init__(self, session: Session) -> None:
        self.session = session
        
    def execute(self, service_id: str, updates: dict[str, Any]) -> ServiceResponseDTO: # TODO: Type Hint the data dict
        try:
            service = self.session.query(Service).filter_by(id=service_id).first()
            if not service:
                raise NotFound("Service not found.")
            for key, value in updates.items():
                if hasattr(service, key):
                    setattr(service, key, value)
            self.session.commit()
            return ServiceResponseDTO.from_model(service)
        except IntegrityError:
            self.session.rollback()
            raise AlreadyExists("A service with that name or slug already exists.")
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError("Database error while updating service.") from e

class DeleteService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, service_id: str) -> None:
        try:
            service = self.session.query(Service).filter_by(id=service_id).first()
            if not service:
                raise NotFound("Service not found.")
            self.session.delete(service)
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError("Database error while deleting service.") from e
    
class GetServicesByCategory:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, category_id: str) -> list[ServiceResponseDTO]:
        try:
            services = self.session.query(Service).filter_by(category_id=category_id).all()
            if not services:
                raise NotFound("No services found in this category.")
            return [ServiceResponseDTO.from_model(service) for service in services]
        except SQLAlchemyError as e:
            raise DatabaseError("Database error while fetching services by category.") from e
    
class GetServiceMix:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, client_id: str) -> list[tuple[str, int]]:

        try:
            rows = (
                self.session.query(ServiceCategory.name, func.count(Order.id))
                .join(Service, Order.service_id == Service.id)
                .join(ServiceCategory, Service.category_id == ServiceCategory.id)
                .filter(Order.client_id == client_id)
                .group_by(ServiceCategory.name)
                .all()
            )
            return [(name, count) for name, count in rows]
        except SQLAlchemyError as exc:
            logger.error("[GetServiceMix] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc


class ServiceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, data: ServiceDTO) -> ServiceResponseDTO:
        return CreateService(self.session).execute(data)

    def get_by_id(self, service_id: str) -> ServiceResponseDTO:
        return GetServiceByID(self.session).execute(service_id)

    def get_by_slug(self, slug: str) -> ServiceResponseDTO:
        return GetServiceBySlug(self.session).execute(slug)

    def get_all(self, active_only: bool = True) -> list[ServiceResponseDTO]:
        return GetAllServices(self.session).execute(active_only)

    def get_featured(self) -> list[ServiceResponseDTO]:
        return GetFeaturedServices(self.session).execute()

    def update(self, service_id: str, updates: dict[str, Any]) -> ServiceResponseDTO: # TODO: Type Hint the data dict
        return UpdateService(self.session).execute(service_id, updates)

    def delete(self, service_id: str) -> None:
        return DeleteService(self.session).execute(service_id)
    def get_services_by_category(self, category_id: str) -> list[ServiceResponseDTO]:
        return GetServicesByCategory(self.session).execute(category_id)

    def get_service_mix(self, client_id: str) -> list[tuple[str, int]]:
        return GetServiceMix(self.session).execute(client_id)