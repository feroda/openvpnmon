from django.core.management.base import BaseCommand, CommandError
from openvpnmon.base.models import Client, ACTION_CLIENT_ENABLED
from openvpnmon.base.models import ClientActionsLog
from openvpnmon.base.management.commands import client_auth

from django.conf import settings
from exceptions import CommandLogError
import os, logging, datetime
import subprocess

log = logging.getLogger('openvpnmon')


class Command(BaseCommand):
    help = 'Set firewall rules'

    def handle(self, *args, **options):
        
        log.info("Setting firewall rules...")
        qs = Client.objects.filter(enabled=True)

        for client in qs:
        
            cmd = client_auth.Command()
            cmd.handle(client.common_name)

        return 0

