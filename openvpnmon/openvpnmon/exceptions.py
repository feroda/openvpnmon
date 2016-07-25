import logging
from django.core.management.base import CommandError

log = logging.getLogger('openvpnmon')


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


class CommandLogError(CommandError):
    def __init__(self, value):
        super(CommandLogError, self).__init__(value)
        log.error(value)
