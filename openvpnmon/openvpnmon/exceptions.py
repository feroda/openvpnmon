class ProgrammingError(Exception):
    pass


class CertNotFound(Exception):
    pass


class CertCreationError(Exception):
    pass


class ClientEnableError(Exception):
    pass


class ClientAuthError(Exception):
    pass


class WrongStateError(Exception):
    pass


class AlreadyRunningError(Exception):
    pass


class NoActiveJobError(Exception):
    pass


class MultipleActiveJobError(Exception):
    pass


class StoppedThreadException(Exception):
    pass
