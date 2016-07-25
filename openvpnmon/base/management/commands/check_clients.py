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


class Command(BaseCommand):
    args = "[client1 name] [client2 name] [...]"
    help = 'Do some sanity checks for clients, and fix inconsistencies. IMPORTANT: client name as input, not certificate "common_name" '

    def handle(self, *args, **options):

        names = args
        l = len(names)

        if not l:
            clients = Client.objects.all()
            log.debug("Sanity check for all clients...")
        else:
            clients = Client.objects.filter(name__in=names)
            if l != clients.count():
                raise CommandError("One or more clients are not found.\n" +
                                   "Clients found are %s." % " ".join(map(
                                       unicode, clients)))

        for client in clients:

            log.debug("Sanity check for client %s..." % client)

            try:
                client.clean_ip()
            except ValidationError as e:
                client.fix_client_ip()

            if not client.cert:
                if client.exist_cert():
                    log.warning("Cert for %s exist, but not bound to client" %
                                client.common_name)
                    client.bind_cert()
                    client.save()
                    log.info("Cert for %s bound to client" %
                             client.common_name)

            wrong_basename = settings.EASY_RSA_KEYS_DIR + client.name + ".crt"
            if os.path.exists(wrong_basename):
                log.warning("(wrong?) cert %s exists" % wrong_basename)

        return 0
