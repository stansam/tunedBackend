from typing import Any, Sequence
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, asc, desc, func
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from tuned.models import Sample
from tuned.dtos.content import(
    SampleDTO, SampleResponseDTO, SampleUpdateDTO,
    SampleListResponseDTO, SampleListRequestDTO
)
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound

class CreateSample:
    def __init__(self, session: Session) -> None:
        self.session = session

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
            self.session.add(sample)
            self.session.flush()
            return SampleResponseDTO.from_model(sample)
        except IntegrityError:
            raise AlreadyExists("A sample with this title or slug already exists.")
        except SQLAlchemyError as e:
            raise DatabaseError("Database error while creating sample.") from e


class GetSampleByID:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, sample_id: str) -> SampleResponseDTO:
        try:
            stmt = select(Sample).where(Sample.id == sample_id)
            sample = self.session.scalar(stmt)
            if not sample:
                raise NotFound("Sample not found.")
            return SampleResponseDTO.from_model(sample)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching sample: {str(e)}") from e


class GetSampleBySlug:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, slug: str) -> SampleResponseDTO:
        try:
            stmt = select(Sample).where(Sample.slug == slug)
            sample = self.session.scalar(stmt)
            if not sample:
                raise NotFound("Sample not found.")
            return SampleResponseDTO.from_model(sample)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching sample: {str(e)}") from e

def getSampleListResponse(
    session: Session, stmt: Any, req: SampleListRequestDTO
) -> SampleListResponseDTO:
    if req.featured:
        stmt = stmt.where(Sample.featured == req.featured)
    if req.service_id:
        stmt = stmt.where(Sample.service_id == req.service_id)
    if req.q:
        search_pattern = f"%{req.q}%"
        stmt = stmt.where(
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

    sort_field = sort_map.get(req.sort or "created_at", Sample.created_at)
    order_func = asc if req.order == "asc" else desc

    stmt = stmt.order_by(order_func(sort_field))

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = session.execute(count_stmt).scalar() or 0

    page = max(req.page or 1, 1)
    per_page = min(req.per_page or 10, 100)

    stmt = stmt.offset((page - 1) * per_page).limit(per_page)
    items: Sequence[Sample] = session.scalars(stmt).all()

    return SampleListResponseDTO(
        samples=[SampleResponseDTO.from_model(s) for s in items],
        total=total,
        page=page,
        per_page=per_page,
        sort=req.sort,
        order=req.order,
    )

class GetAllSamples:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self) -> list[SampleResponseDTO]:
        try:
            stmt = select(Sample)
            samples = self.session.scalars(stmt).all()
            return [SampleResponseDTO.from_model(s) for s in samples]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching samples: {str(e)}") from e

class ListAllSamples:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, req: SampleListRequestDTO) -> SampleListResponseDTO:
        try:
            stmt = select(Sample)
            return getSampleListResponse(self.session, stmt, req)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching samples: {str(e)}") from e

class GetFeaturedSamples:
    def __init__(self, session: Session) -> None:
        self.session = session
    
    def execute(self) -> list[SampleResponseDTO]:
        try:
            stmt = (
                select(Sample)
                .where(Sample.featured == True)
                .order_by(Sample.created_at.desc())
            )
            samples = self.session.scalars(stmt).all()
            return [SampleResponseDTO.from_model(s) for s in samples]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching featured samples: {str(e)}") from e

class UpdateSample:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, sample_id: str, updates: SampleUpdateDTO) -> SampleResponseDTO:
        try:
            stmt = select(Sample).where(Sample.id == sample_id)
            sample = self.session.scalar(stmt)
            if not sample:
                raise NotFound("Sample not found.")
            update_data = {k: v for k, v in updates.__dict__.items() if v is not None}
            for key, value in update_data.items():
                if hasattr(sample, key):
                    setattr(sample, key, value)
            self.session.flush()
            return SampleResponseDTO.from_model(sample)
        except IntegrityError:
            raise AlreadyExists("A sample with that title or slug already exists.")
        except SQLAlchemyError as e:
            raise DatabaseError("Database error while updating sample.") from e


class DeleteSample:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, sample_id: str) -> None:
        try:
            stmt = select(Sample).where(Sample.id == sample_id)
            sample = self.session.scalar(stmt)
            if not sample:
                raise NotFound("Sample not found.")
            self.session.delete(sample)
            self.session.flush()
        except SQLAlchemyError as e:
            raise DatabaseError("Database error while deleting sample.") from e

class GetSamplesByServiceId:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, service_id: str) -> list[SampleResponseDTO]:
        try:
            stmt = select(Sample).where(Sample.service_id == service_id)
            samples = self.session.scalars(stmt).all()
            return [SampleResponseDTO.from_model(s) for s in samples]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching samples: {str(e)}") from e


from tuned.repository.protocols import SampleRepositoryProtocol

class SampleRepository(SampleRepositoryProtocol):
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, data: SampleDTO) -> SampleResponseDTO:
        return CreateSample(self.session).execute(data)

    def get_by_id(self, sample_id: str) -> SampleResponseDTO:
        return GetSampleByID(self.session).execute(sample_id)

    def get_by_slug(self, slug: str) -> SampleResponseDTO:
        return GetSampleBySlug(self.session).execute(slug)
    
    def get_featured(self) -> list[SampleResponseDTO]:
        return GetFeaturedSamples(self.session).execute()

    def get_all(self) -> list[SampleResponseDTO]:
        return GetAllSamples(self.session).execute()
    
    def list_all(
        self,
        req: SampleListRequestDTO
    ) -> SampleListResponseDTO:
        return ListAllSamples(self.session).execute(req)

    def update(self, sample_id: str, updates: SampleUpdateDTO) -> SampleResponseDTO:
        return UpdateSample(self.session).execute(sample_id, updates)

    def delete(self, sample_id: str) -> None:
        return DeleteSample(self.session).execute(sample_id)

    def get_samples_by_service_id(self, service_id: str) -> list[SampleResponseDTO]:
        return GetSamplesByServiceId(self.session).execute(service_id)