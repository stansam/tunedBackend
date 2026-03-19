import re
import unicodedata
from sqlalchemy.orm import Session
from sqlalchemy import select

def generate_slug(title: str, model, session: Session, max_length: int = 100)-> str:
    normalized = unicodedata.normalize("NFKD", title)
    ascii_title = normalized.encode("ascii", "ignore").decode("ascii")

    base_slug = re.sub(r"[^\w\s-]", "", ascii_title.lower())
    base_slug = re.sub(r"[-\s]+", "-", base_slug).strip("-")
    base_slug = base_slug[:max_length].strip("-")

    if not base_slug:
        raise ValueError(f"Could not generate a valid slug from title: {title!r}")

    slug = base_slug
    counter = 1
    while session.execute(select(model).filter_by(slug=slug)).first() is not None:
        suffix = f"-{counter}"
        slug = f"{base_slug[:max_length - len(suffix)]}{suffix}"
        counter += 1

    return slug