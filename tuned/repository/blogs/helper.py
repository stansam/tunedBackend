from tuned.models import Tag
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

def handle_tags(tags:list, db:Session)-> list:
    tags_list = []
    for tag_name in tags:
        tag = db.query(Tag).filter_by(name=tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            db.add(tag)

            try:
                db.flush()
            except IntegrityError:
                db.rollback()
                tag = db.query(Tag).filter_by(name=tag_name).first()
        tags_list.append(tag)
    return tags_list
        
    