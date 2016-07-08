from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import PermissionDenied, ValidationError

from openvpnmon.base.management.commands import client_enable
from openvpnmon.base.models import Client
from openvpnmon.base import netutils

from django.conf import settings
from exceptions import CommandLogError
import os, logging, datetime
import subprocess

log = logging.getLogger('openvpnmon')


class Command(BaseCommand):
    args = "[client1 common name] [client2 common name] [...]"
    help = 'Do some sanity checks for clients, and fix inconsistencies'

    def handle(self, *args, **options):

        common_names = args
        l = len(common_names)

        if not l:
            clients = Client.objects.all()
            log.debug("Sanity check for all clients...")
        else:
            clients = Client.objects.filter(common_name__in=common_names)
            if l != clients.count():
                raise CommandError("One or more clients are not found.\n" +
                                   "Clients found are %s." % " ".join(map(
                                       unicode, clients)))

            log.debug("Sanity check for clients %s..." % common_names)

        for client in clients:

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

        return 0
