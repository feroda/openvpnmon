from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import PermissionDenied, ValidationError

from base.management.commands import client_enable
from base.models import Client
from base import netutils

from django.conf import settings
from openvpnmon.exceptions import CommandLogError
import os, logging, datetime
import subprocess

log = logging.getLogger('openvpnmon')
if settings.LOG_FILE:

    if not log.handlers:
        log.setLevel(logging.INFO)
        hdlr = logging.FileHandler(settings.LOG_FILE)
        hdlr.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s %(message)s'))
        log.addHandler(hdlr)


class Command(BaseCommand):
    args = ""
    help = 'Do some sanity checks for clients, and fix inconsistencies'

    def handle(self, *args, **options):

        log.debug("Checking clients ip addresses...")

        for client in Client.objects.all():
            try:
                client.clean_ip()
            except ValidationError, e:
                client.fix_client_ip()

            if not client.cert:
                if client.exist_cert():
                    log.warning("Cert for %s exist, but not bound to client" %
                                client.common_name)
                    client.bind_cert()
                    client.save()
                    log.info("Cert for %s bound to client" %
                             client.common_name)

        return 0
