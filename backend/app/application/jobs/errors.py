from app.application.errors import ApplicationError


class JobNotFoundError(ApplicationError):
    pass


class JobDispatchError(ApplicationError):
    pass


class DummyJobExecutionError(ApplicationError):
    pass
