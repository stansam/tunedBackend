from tuned.models import Tag
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

def handle_tags(tags: list[str], session: Session)-> list[Tag]:
    tags_list = []
    for tag_name in tags:
        clean_name = tag_name.strip().lower()
        stmt = select(Tag).where(Tag.name == clean_name)
        tag = session.scalar(stmt)
        if not tag:
            try:
                with session.begin_nested():
                    tag = Tag(name=clean_name)
                    session.add(tag)
                    session.flush()
            except IntegrityError:
                stmt = select(Tag).where(Tag.name == clean_name)
                tag = session.scalar(stmt)
        if tag:
            tags_list.append(tag)
    return tags_list