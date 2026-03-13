from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from tuned.extensions import db
from tuned.models import Service
from tuned.models.service import ServiceCategory
from tuned.dtos.services import ServiceDTO, ServiceCategoryDTO
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound


# ---------------------------------------------------------------------------
# Service commands
# ---------------------------------------------------------------------------

class CreateService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, data: ServiceDTO) -> Service:
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
            return service
        except IntegrityError:
            self.db.session.rollback()
            raise AlreadyExists("A service with this name or slug already exists.")
        except SQLAlchemyError as e:
            self.db.session.rollback()
            raise DatabaseError("Database error while creating service.") from e


class GetServiceByID:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, service_id: str) -> Service:
        try:
            service = self.db.session.query(Service).filter_by(id=service_id).first()
            if not service:
                raise NotFound("Service not found.")
            return service
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching service: {str(e)}") from e


class GetServiceBySlug:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, slug: str) -> Service:
        try:
            service = self.db.session.query(Service).filter_by(slug=slug).first()
            if not service:
                raise NotFound("Service not found.")
            return service
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching service: {str(e)}") from e


class GetAllServices:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, active_only: bool = True) -> list[Service]:
        try:
            query = self.db.session.query(Service)
            if active_only:
                query = query.filter_by(is_active=True)
            return query.order_by(Service.name.asc()).all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching services: {str(e)}") from e


class GetFeaturedServices:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self) -> list[Service]:
        try:
            return (
                self.db.session.query(Service)
                .filter_by(featured=True, is_active=True)
                .order_by(Service.name.asc())
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching featured services: {str(e)}") from e


class UpdateService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, service_id: str, updates: dict) -> Service:
        try:
            service = self.db.session.query(Service).filter_by(id=service_id).first()
            if not service:
                raise NotFound("Service not found.")
            for key, value in updates.items():
                if hasattr(service, key):
                    setattr(service, key, value)
            self.db.session.commit()
            return service
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


# ---------------------------------------------------------------------------
# ServiceCategory commands
# ---------------------------------------------------------------------------

class CreateServiceCategory:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, data: ServiceCategoryDTO) -> ServiceCategory:
        try:
            category = ServiceCategory(
                name=data.name,
                description=data.description,
                order=data.order,
            )
            self.db.session.add(category)
            self.db.session.commit()
            return category
        except IntegrityError:
            self.db.session.rollback()
            raise AlreadyExists("A service category with this name already exists.")
        except SQLAlchemyError as e:
            self.db.session.rollback()
            raise DatabaseError("Database error while creating service category.") from e


class GetServiceCategoryByID:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, category_id: str) -> ServiceCategory:
        try:
            category = self.db.session.query(ServiceCategory).filter_by(id=category_id).first()
            if not category:
                raise NotFound("Service category not found.")
            return category
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching service category: {str(e)}") from e


class GetAllServiceCategories:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self) -> list[ServiceCategory]:
        try:
            return (
                self.db.session.query(ServiceCategory)
                .order_by(ServiceCategory.order.asc())
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching service categories: {str(e)}") from e


class UpdateServiceCategory:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, category_id: str, updates: dict) -> ServiceCategory:
        try:
            category = self.db.session.query(ServiceCategory).filter_by(id=category_id).first()
            if not category:
                raise NotFound("Service category not found.")
            for key, value in updates.items():
                if hasattr(category, key):
                    setattr(category, key, value)
            self.db.session.commit()
            return category
        except IntegrityError:
            self.db.session.rollback()
            raise AlreadyExists("A service category with that name already exists.")
        except SQLAlchemyError as e:
            self.db.session.rollback()
            raise DatabaseError("Database error while updating service category.") from e


class DeleteServiceCategory:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, category_id: str) -> None:
        try:
            category = self.db.session.query(ServiceCategory).filter_by(id=category_id).first()
            if not category:
                raise NotFound("Service category not found.")
            self.db.session.delete(category)
            self.db.session.commit()
        except SQLAlchemyError as e:
            self.db.session.rollback()
            raise DatabaseError("Database error while deleting service category.") from e


# ---------------------------------------------------------------------------
# Repository facades
# ---------------------------------------------------------------------------

class ServiceRepository:
    """Facade that composes all service command objects."""

    def __init__(self) -> None:
        self.db = db

    def create(self, data: ServiceDTO) -> Service:
        return CreateService(self.db).execute(data)

    def get_by_id(self, service_id: str) -> Service:
        return GetServiceByID(self.db).execute(service_id)

    def get_by_slug(self, slug: str) -> Service:
        return GetServiceBySlug(self.db).execute(slug)

    def get_all(self, active_only: bool = True) -> list[Service]:
        return GetAllServices(self.db).execute(active_only)

    def get_featured(self) -> list[Service]:
        return GetFeaturedServices(self.db).execute()

    def update(self, service_id: str, updates: dict) -> Service:
        return UpdateService(self.db).execute(service_id, updates)

    def delete(self, service_id: str) -> None:
        return DeleteService(self.db).execute(service_id)


class ServiceCategoryRepository:
    """Facade that composes all service-category command objects."""

    def __init__(self) -> None:
        self.db = db

    def create(self, data: ServiceCategoryDTO) -> ServiceCategory:
        return CreateServiceCategory(self.db).execute(data)

    def get_by_id(self, category_id: str) -> ServiceCategory:
        return GetServiceCategoryByID(self.db).execute(category_id)

    def get_all(self) -> list[ServiceCategory]:
        return GetAllServiceCategories(self.db).execute()

    def update(self, category_id: str, updates: dict) -> ServiceCategory:
        return UpdateServiceCategory(self.db).execute(category_id, updates)

    def delete(self, category_id: str) -> None:
        return DeleteServiceCategory(self.db).execute(category_id)
