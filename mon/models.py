from django.db import models
from django.utils.translation import ugettext, ugettext_lazy as _
from django.db.models import Q
from django.template.defaultfilters import slugify
import subprocess, os, datetime
from django.conf import settings
from django.core.exceptions import PermissionDenied

from base.models import Client


class OpenVPNLog(models.Model):

    common_name = models.CharField(max_length=128)
    public_ip = models.GenericIPAddressField(_('IP address'))
    vpn_ip = models.GenericIPAddressField(_('VPN IP address'), db_index=True)
    vpn_iface = models.CharField(_('VPN iface'), max_length=8, db_index=True)
    when_connect = models.DateTimeField()
    when_disconnect = models.DateTimeField(null=True)
    bytes_sent = models.PositiveIntegerField(null=True, default=None)
    bytes_received = models.PositiveIntegerField(null=True, default=None)

    class Meta:
        ordering = ["-when_connect"]
        get_latest_by = "when_connect"
        verbose_name = "OpenVPN log"

    def __unicode__(self):
        return "%s from %s assigned IP %s connected on %s, disconnected on %s" % (
            self.common_name, self.public_ip, self.vpn_ip, self.when_connect,
            self.when_disconnect)
