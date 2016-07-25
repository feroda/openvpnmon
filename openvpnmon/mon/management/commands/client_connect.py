from django.core.management.base import BaseCommand, CommandError
from base.models import Client
from mon.models import OpenVPNLog

from django.conf import settings
from openvpnmon.exceptions import CommandLogError
import os, logging, datetime

NO_ENV_MESSAGE = "YOU ARE NOT CALLING THIS SCRIPT FROM \
client-connect OPENVPN DIRECTIVE. \
You lack of some environmental variables."

log = logging.getLogger('openvpnmon')

if not log.handlers:
    log.setLevel(logging.INFO)
    hdlr = logging.FileHandler(settings.LOG_FILE)
    hdlr.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s %(message)s'))
    log.addHandler(hdlr)


class Command(BaseCommand):
    help = 'To be used in client-connect directive argument on openvpn.conf. Adds an entry to OpenVPN logs table.'

    def handle(self, *args, **options):

        log.info("Starting connection script")
        try:
            common_name = os.environ['common_name']
        except KeyError:
            raise CommandLogError(NO_ENV_MESSAGE)
        try:
            client = Client.objects.get(common_name=common_name)
        except Client.DoesNotExist:
            if settings.HARDENING:
                # OpenVPNMon is also a security feature
                raise CommandError(
                    "Common name %s has not been enabled to access the VPN" %
                    common_name)
            else:
                # Client is automagically inserted in clients list
                client = Client(ip=os.environ['ifconfig_pool_remote_ip'],
                                common_name=common_name, )
                client.save()

        try:
            log_entry = OpenVPNLog(
                common_name=common_name,
                public_ip=os.environ['trusted_ip'],
                vpn_ip=os.environ['ifconfig_pool_remote_ip'],
                vpn_iface=os.environ['dev'],
                when_connect=datetime.datetime.fromtimestamp(int(os.environ[
                    'time_unix'])), )
        except KeyError:
            raise CommandLogError(NO_ENV_MESSAGE)

        log_entry.save()
        log.info("Saved log_entry: %s" % log_entry)

        return 0
