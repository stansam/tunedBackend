from tuned.models import Tag
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

def handle_tags(tags: list[str], db: Session)-> list[Tag]:
    tags_list = []
    for tag_name in tags:
        clean_name = tag_name.strip().lower()
        tag = db.query(Tag).filter_by(name=clean_name).first()
        if not tag:
            try:
                with db.begin_nested():
                    tag = Tag(name=clean_name)  # type: ignore[no-untyped-call]
                    db.add(tag)
            except IntegrityError:
                tag = db.query(Tag).filter_by(name=clean_name).first()
        if tag:
            tags_list.append(tag)
    return tags_list