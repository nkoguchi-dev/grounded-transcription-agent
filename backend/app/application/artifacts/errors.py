from app.application.errors import ApplicationError


class ArtifactNotFoundError(ApplicationError):
    pass


class ArtifactObjectNotFoundError(ApplicationError):
    pass


class ArtifactNotReadyError(ApplicationError):
    pass


class ObjectStorageUnavailableError(ApplicationError):
    pass
