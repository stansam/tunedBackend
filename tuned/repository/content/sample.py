from sqlalchemy.orm import Session, Query
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from sqlalchemy import or_, asc, desc
from tuned.extensions import db
from tuned.models import Sample
from tuned.dtos.content import(
    SampleDTO, SampleResponseDTO,
    SampleListResponseDTO, SampleListRequestDTO
)
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound

class CreateSample:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, data: SampleDTO) -> SampleResponseDTO:
        try:
            sample = Sample(
                title=data.title,
                content=data.content,
                service_id=data.service_id,
                excerpt=data.excerpt,
                word_count=data.word_count,
                featured=data.featured,
                image=data.image,
                slug=data.slug or None,
            )
            self.db.session.add(sample)
            self.db.session.commit()
            return SampleResponseDTO.from_model(sample)
        except IntegrityError:
            self.db.session.rollback()
            raise AlreadyExists("A sample with this title or slug already exists.")
        except SQLAlchemyError as e:
            self.db.session.rollback()
            raise DatabaseError("Database error while creating sample.") from e


class GetSampleByID:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, sample_id: str) -> SampleResponseDTO:
        try:
            sample = self.db.session.query(Sample).filter_by(id=sample_id).first()
            if not sample:
                raise NotFound("Sample not found.")
            return SampleResponseDTO.from_model(sample)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching sample: {str(e)}") from e


class GetSampleBySlug:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, slug: str) -> SampleResponseDTO:
        try:
            sample = self.db.session.query(Sample).filter_by(slug=slug).first()
            if not sample:
                raise NotFound("Sample not found.")
            return SampleResponseDTO.from_model(sample)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching sample: {str(e)}") from e

def getSampleListResponse(
    query: Query[Sample], req: SampleListRequestDTO
) -> SampleListResponseDTO:
    if req.featured:
        query = query.filter_by(featured=req.is_featured)
    if req.service_id:
        query = query.filter_by(service_id=req.service_id)
    if req.q:
        search_pattern = f"%{req.q}%"
        query = query.filter(
            or_(
                Sample.title.ilike(search_pattern),
                Sample.excerpt.ilike(search_pattern),
                Sample.content.ilike(search_pattern)
            )
        )

    sort_map = {
        "created_at": Sample.created_at,
        "title": Sample.title,
    }

    sort_field = sort_map.get(req.sort, Sample.created_at)
    order_func = asc if req.order == "asc" else desc

    query = query.order_by(order_func(sort_field))

    total = query.order_by(None).count()

    page = max(req.page or 1, 1)
    per_page = min(req.per_page or 10, 100)

    items = query.offset((page - 1) * per_page).limit(per_page).all()

    return SampleListResponseDTO(
        samples=[SampleResponseDTO.from_model(s) for s in items],
        total=total,
        page=page,
        per_page=per_page,
        sort=req.sort,
        order=req.order,
    )

class GetAllSamples:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self) -> list[SampleResponseDTO]:
        try:
            samples = self.db.session.query(Sample).all()
            if not samples:
                samples = []
            
            return [SampleResponseDTO.from_model(s) for s in samples]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching samples: {str(e)}") from e

class ListAllSamples:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, req: SampleListRequestDTO) -> SampleListResponseDTO:
        try:
            query = self.db.session.query(Sample)
            samples = getSampleListResponse(query, req)
            if not samples:
                samples = []
            
            return samples
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching samples: {str(e)}") from e
class GetFeaturedSamples:
    def __init__(self, db: Session) -> None:
        self.db = db
    
    def execute(self) -> list[SampleResponseDTO]:
        try:
            samples = self.db.session.query(Sample).filter_by(featured=True).order_by(Sample.created_at.desc()).all()
            return [SampleResponseDTO.from_model(s) for s in samples]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching featured samples: {str(e)}") from e

class UpdateSample:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, sample_id: str, updates: dict) -> SampleResponseDTO:
        try:
            sample = self.db.session.query(Sample).filter_by(id=sample_id).first()
            if not sample:
                raise NotFound("Sample not found.")
            for key, value in updates.items():
                if hasattr(sample, key):
                    setattr(sample, key, value)
            self.db.session.commit()
            return SampleResponseDTO.from_model(sample)
        except IntegrityError:
            self.db.session.rollback()
            raise AlreadyExists("A sample with that title or slug already exists.")
        except SQLAlchemyError as e:
            self.db.session.rollback()
            raise DatabaseError("Database error while updating sample.") from e


class DeleteSample:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, sample_id: str) -> None:
        try:
            sample = self.db.session.query(Sample).filter_by(id=sample_id).first()
            if not sample:
                raise NotFound("Sample not found.")
            self.db.session.delete(sample)
            self.db.session.commit()
        except SQLAlchemyError as e:
            self.db.session.rollback()
            raise DatabaseError("Database error while deleting sample.") from e

class GetSamplesByServiceId:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, service_id: str) -> list[SampleResponseDTO]:
        try:
            samples = self.db.session.query(Sample).filter_by(service_id=service_id).all()
            return [SampleResponseDTO.from_model(s) for s in samples]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching samples: {str(e)}") from e


class SampleRepository:
    """Facade composing all Sample command objects."""

    def __init__(self) -> None:
        self.db = db

    def create(self, data: SampleDTO) -> SampleResponseDTO:
        return CreateSample(self.db).execute(data)

    def get_by_id(self, sample_id: str) -> SampleResponseDTO:
        return GetSampleByID(self.db).execute(sample_id)

    def get_by_slug(self, slug: str) -> SampleResponseDTO:
        return GetSampleBySlug(self.db).execute(slug)
    
    def get_featured(self) -> list[SampleResponseDTO]:
        return GetFeaturedSamples(self.db).execute()

    def get_all(self) -> list[SampleResponseDTO]:
        return GetAllSamples(self.db).execute()
    
    def list_all(
        self,
        req: SampleListRequestDTO
    ) -> list[SampleResponseDTO]:
        return ListAllSamples(self.db).execute(req)

    def update(self, sample_id: str, updates: dict) -> SampleResponseDTO:
        return UpdateSample(self.db).execute(sample_id, updates)

    def delete(self, sample_id: str) -> None:
        return DeleteSample(self.db).execute(sample_id)

    def get_samples_by_service_id(self, service_id: str) -> list[SampleResponseDTO]:
        return GetSamplesByServiceId(self.db).execute(service_id)