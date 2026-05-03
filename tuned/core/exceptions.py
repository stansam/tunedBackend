class DatabaseError(Exception):
    pass

class ServiceError(Exception):
    pass

class NotFound(Exception):
    pass

class AlreadyExists(Exception):
    pass

class InvalidCredentials(Exception):
    pass