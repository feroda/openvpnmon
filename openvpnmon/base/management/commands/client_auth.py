from django.core.management.base import BaseCommand, CommandError
from base.models import Client, ACTION_CLIENT_AUTHORIZATION_UPDATE, ACTION_ERROR_CLIENT_AUTHORIZE
from base.models import ClientActionsLog
from openvpnmon.utils import call_shell, CalledShellCommandError
from openvpnmon.exceptions import ClientAuthError

from django.conf import settings
from openvpnmon.exceptions import CommandLogError
import os, logging, datetime
import subprocess

log = logging.getLogger('openvpnmon')


class Command(BaseCommand):
    args = "<client cert common name>"
    help = 'Update client authorization to connect to other clients'

    def handle(self, *args, **options):

        try:
            common_name = args[0]
        except:
            raise CommandError("Usage client_enable %s" % (self.args))

        try:
            client = Client.objects.get(common_name=common_name)
        except Client.DoesNotExist:
            raise CommandError(
                "You should specify a common_name af an already existent host in OpenVPNmon database")
        log.info(u"AUTHORIZING %s" % common_name)

        cmd = [
            settings.HOOK_CLIENT_MANAGE,
            'access-flush',
            client.subnet.bound_iface,
            client.ip,
        ]
        shell_cmd = " ".join(cmd)

        log.info(u"Removing rules for %s: iface %s, ip: %s" %
                 (client, client.subnet.bound_iface, client.ip))
        try:
            out = call_shell(shell_cmd)
        except CalledShellCommandError as e:
            error_log = "%s | return code %s | %s" % (e.shell_cmd,
                                                      e.returncode, e.output)
            log.debug(error_log)
            client_log = ClientActionsLog(action=ACTION_ERROR_CLIENT_AUTHORIZE,
                                          note=error_log)
            client.clientactionslog_set.add(client_log)
            raise CommandError(e.output)

        for to_client in client.can_access_to.all():
            # Adds a firewall rule for each client, the client must be able to reach.
            # NOTE: IF YOU DO NOT SPECITY CLIENTS THAN CAN BE ACCESSED, THEN 
            # EVERY CLIENT IN THE DESTINATION NETWORK CAN BE REACHED
            Cmd = [
                settings.HOOK_CLIENT_MANAGE,
                'access-allow',
                client.subnet.bound_iface,
                client.ip,
                to_client.subnet.bound_iface,
                to_client.ip,
            ]
            shell_cmd = " ".join(cmd)
            try:
                call_shell(shell_cmd)
            except CalledShellCommandError as e:
                error_log = "%s | return code %s | %s" % (
                    e.shell_cmd, e.returncode, e.output)
                log.debug(error_log)
                client_log = ClientActionsLog(
                    action=ACTION_ERROR_CLIENT_AUTHORIZE,
                    note=error_log)
                client.clientactionslog_set.add(client_log)
                raise ClientEnableError(e.output)

            log.info(u"EXECUTED: %s" % shell_cmd)

        log_entry = ClientActionsLog(client=client,
                                     action=ACTION_CLIENT_AUTHORIZATION_UPDATE,
                                     remote_ip="127.0.0.1", )

        log_entry.save()
        log.info(u"Saved log_entry: %s" % log_entry)

        return 0
