class ContentException(Exception):
    """Base exception for the content repository layer."""
    pass


class DatabaseError(ContentException):
    """Raised when an unexpected SQLAlchemy error occurs."""
    pass


class NotFound(ContentException):
    """Raised when a requested resource is not found."""
    pass


class AlreadyExists(ContentException):
    """Raised when attempting to create a resource that already exists."""
    pass
