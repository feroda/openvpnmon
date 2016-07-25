from django.core.management.base import BaseCommand, CommandError
from base.models import Client
from mon.models import OpenVPNLog
from django.conf import settings

import os, logging, datetime
from openvpnmon.exceptions import CommandLogError

NO_ENV_MESSAGE = "YOU ARE NOT CALLING THIS SCRIPT FROM \
client-disconnect OPENVPN DIRECTIVE. \
You lack of some environmental variables."

log = logging.getLogger('openvpnmon')
if not log.handlers:

    log.setLevel(logging.INFO)
    hdlr = logging.FileHandler(settings.LOG_FILE)
    hdlr.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s %(message)s'))
    log.addHandler(hdlr)


class Command(BaseCommand):
    args = ''
    help = 'To be used in client-disconnect directive argument on openvpn.conf. Adds some info to connection entry in OpenVPN logs table.'

    def handle(self, *args, **options):

        try:
            common_name = os.environ['common_name']
        except KeyError:
            raise CommandLogError(NO_ENV_MESSAGE)
        try:
            client = Client.objects.get(common_name=common_name)
        except Client.DoesNotExits:
            raise CommandError(
                "Common name %s has not been enabled to access the VPN" %
                common_name)

        try:
            log_entry = OpenVPNLog.objects.filter(
                common_name=common_name,
                when_disconnect__isnull=True).latest()
            log_entry.bytes_sent = int(os.environ['bytes_sent'])
            log_entry.bytes_received = int(os.environ['bytes_received'])
            log_entry.when_disconnect = datetime.datetime.fromtimestamp(int(
                os.environ['time_duration']) + int(os.environ['time_unix']))
        except KeyError:
            raise CommandLogError(NO_ENV_MESSAGE)

        log_entry.save()
        log.info("Saved log_entry: %s" % log_entry)

        return 0
