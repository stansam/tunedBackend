class RepositoryException(Exception):
    pass

class DatabaseError(Exception):
    pass

class NotFound(Exception):
    pass

class ValidationError(Exception):
    pass

class AlreadyExists(Exception):
    pass

class InvalidCredentials(Exception):
    pass