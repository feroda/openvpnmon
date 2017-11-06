from django.core.management.base import BaseCommand, CommandError
from base.models import Client, ACTION_CLIENT_ENABLED, ACTION_ERROR_CLIENT_ENABLE
from base.models import ClientActionsLog
from base.management.commands import client_auth
from openvpnmon.utils import call_shell, CalledShellCommandError
from openvpnmon.exceptions import ClientEnableError

from django.conf import settings
from openvpnmon.exceptions import CommandLogError

import os, logging, datetime
import subprocess

log = logging.getLogger(__name__)


class Command(BaseCommand):
    args = "<client cert common name>"
    help = 'Enable a client to access VPN. It must be invoked by root'

    def add_arguments(self, parser):
        parser.add_argument('CN')


    def handle(self, *args, **options):

        try:
            common_name = options['CN']
        except:
            raise CommandError("Usage client_enable %s" % (self.args))

        log.info("Enabling client %s" % common_name)
        try:
            client = Client.objects.get(common_name=common_name)
        except Client.DoesNotExist:
            raise CommandError(
                "You should specify a common_name af an already existent host in OpenVPNmon database")

        if client.enabled:
            raise CommandError("Client %s has already been enabled" % client)

        cmd = [
            settings.HOOK_CLIENT_MANAGE,
            'enable',
            client.common_name,
            client.subnet.name,
            client.ip,
            client.subnet.dotted_quad_netmask(),
        ]

        shell_cmd = " ".join(cmd)
        log.info("EXECUTING: %s" % shell_cmd)
        try:
            call_shell(shell_cmd)
        except CalledShellCommandError as e:
            error_log = "%s | return code %s | %s" % (e.shell_cmd,
                                                      e.returncode, e.output)
            log.debug(error_log)
            client.save()
            log_entry = ClientActionsLog(client=client,
                                         action=ACTION_ERROR_CLIENT_ENABLE,
                                         note=error_log)

            log_entry.save()
            raise CommandError(e.output)

        log.info("ENABLING -> CLIENT AUTH")
        #cmd = client_auth.Command()
        #cmd.handle(common_name)

        client.enabled = True
        client.save()

        log_entry = ClientActionsLog(client=client,
                                     action=ACTION_CLIENT_ENABLED,
                                     remote_ip="127.0.0.1", )

        log_entry.save()
        log.info("Saved log_entry: %s" % log_entry)

        return 0
