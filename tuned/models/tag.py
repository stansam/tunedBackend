from sqlalchemy.orm import Mapped, mapped_column, relationship, Query
from tuned.extensions import db
from tuned.models.utils import generate_slug
from datetime import datetime, timezone
from tuned.models.base import BaseModel
from typing import TYPE_CHECKING, Optional, Any

if TYPE_CHECKING:
    from tuned.models.service import Service
    from tuned.models.content import Sample
    from tuned.models.blog import BlogPost

service_tags = db.Table('service_tags',
    db.Column('service_id', db.String(36), db.ForeignKey('service.id'), primary_key=True),
    db.Column('tag_id', db.String(36), db.ForeignKey('tag.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=lambda: datetime.now(timezone.utc))
)

sample_tags = db.Table('sample_tags',
    db.Column('sample_id', db.String(36), db.ForeignKey('sample.id'), primary_key=True),
    db.Column('tag_id', db.String(36), db.ForeignKey('tag.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=lambda: datetime.now(timezone.utc))
)

blog_post_tags = db.Table('blog_post_tags',
    db.Column('blog_post_id', db.String(36), db.ForeignKey('blog_post.id'), primary_key=True),
    db.Column('tag_id', db.String(36), db.ForeignKey('tag.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=lambda: datetime.now(timezone.utc))
)

class Tag(BaseModel):
    __tablename__ = 'tag'
    
    name: Mapped[str] = mapped_column(db.String(50), unique=True, nullable=False, index=True)
    slug: Mapped[str] = mapped_column(db.String(60), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(db.String(200), nullable=True)
    usage_count: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    
    services: Mapped[list["Service"]] = relationship('Service', secondary=service_tags, back_populates='tag_list', lazy='selectin')
    samples: Mapped[list["Sample"]] = relationship('Sample', secondary=sample_tags, lazy='selectin', back_populates='tag_list')
    blog_posts: Mapped[list["BlogPost"]] = relationship('BlogPost', secondary=blog_post_tags, lazy='selectin', back_populates='tag_list')
    
    def __init__(self, name: str, description: Optional[str]=None, **kwargs: Any) -> None:
        super(Tag, self).__init__(**kwargs)
        self.name = name.strip().lower() if name else name
        self.description = description
        if not self.slug and self.name:
            self.slug = self.generate_slug(self.name)
    
    def generate_slug(self, name: str) -> str:
        return generate_slug(name, Tag, db.session)
    
    def increment_usage(self) -> None:
        self.usage_count += 1
        db.session.commit()
    
    def decrement_usage(self) -> None:
        if self.usage_count > 0:
            self.usage_count -= 1
            db.session.commit()
    
    @staticmethod
    def get_or_create(tag_name: str) -> "Tag":
        from sqlalchemy.exc import IntegrityError
        clean_name = tag_name.strip().lower()
        tag = Tag.query.filter_by(name=clean_name).first()
        if not tag:
            try:
                with db.session.begin_nested():
                    tag = Tag(name=clean_name)
                    db.session.add(tag)
            except IntegrityError:
                tag = Tag.query.filter_by(name=clean_name).first()
        return tag  # type: ignore[no-any-return]
    
    @staticmethod
    def parse_tags(tag_string: str) -> list["Tag"]:
        if not tag_string:
            return []
        
        tag_names = [t.strip() for t in tag_string.split(',') if t.strip()]
        tags = []
        for name in tag_names:
            tag = Tag.get_or_create(name)
            tags.append(tag)
        return tags
    
    def __repr__(self) -> str:
        return f'<Tag {self.name}>'
