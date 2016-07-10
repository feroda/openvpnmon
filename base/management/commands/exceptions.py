from django.core.management.base import CommandError

import logging

log = logging.getLogger('openvpnmon')

class CommandLogError(CommandError):

    def __init__(self, value):
        super(CommandLogError, self).__init__(value)
        log.error(value)

