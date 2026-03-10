class DatabaseError(UserServiceException):
    pass

class NotFound(UserServiceException):
    pass

class AlreadyExists(UserServiceException):
    pass
