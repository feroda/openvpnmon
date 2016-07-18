import subprocess
import os
import datetime
import logging

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import slugify
from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError

from openvpnmon.utils import call_shell, CalledShellCommandError
from openvpnmon.exceptions import CertNotFound, CertCreationError

import netutils
import tokens

ACTION_CLIENT_ENABLED = "CLIENT ENABLED"
ACTION_CLIENT_AUTHORIZATION_UPDATE = "CLIENT AUTHORIZATION UPDATE"
ACTION_CERT_CREATED = "CERT CREATED"
ACTION_CERT_DISTRIBUTED = "CERT DISTRIBUTED"
ACTION_CERT_REVOKED = "CERT REVOKED"
ACTION_CERT_DOWNLOADED = "CERT DOWNLOADED"
ACTION_CERT_DISTRIBUTION_TOKEN_CHECKED = "CERT DISTRIBUTION TOKEN CHECKED"

ACTION_ERROR_CERT_CREATE = "ERROR ON CERT CREATE"
ACTION_ERROR_CLIENT_ENABLE = "ERROR ON CLIENT ENABLE"
ACTION_ERROR_CLIENT_AUTHORIZE = "ERROR ON CLIENT AUTHORIZE"
ACTION_ERROR = "ERROR"

ACTIONS_ERROR_LIST = [
    (ACTION_ERROR_CERT_CREATE, ACTION_ERROR_CERT_CREATE),
    (ACTION_ERROR_CLIENT_ENABLE, ACTION_ERROR_CLIENT_ENABLE),
    (ACTION_ERROR_CLIENT_AUTHORIZE, ACTION_ERROR_CLIENT_AUTHORIZE),
    (ACTION_ERROR, ACTION_ERROR),
]

ACTIONS_LIST = [
    (ACTION_CLIENT_ENABLED, ACTION_CLIENT_ENABLED),
    (ACTION_CLIENT_AUTHORIZATION_UPDATE, ACTION_CLIENT_AUTHORIZATION_UPDATE),
    (ACTION_CERT_CREATED, ACTION_CERT_CREATED),
    (ACTION_CERT_DISTRIBUTED, ACTION_CERT_DISTRIBUTED),
    (ACTION_CERT_DISTRIBUTION_TOKEN_CHECKED,
     ACTION_CERT_DISTRIBUTION_TOKEN_CHECKED),
    (ACTION_CERT_REVOKED, ACTION_CERT_REVOKED),
    (ACTION_CERT_DOWNLOADED, ACTION_CERT_DOWNLOADED),
] + ACTIONS_ERROR_LIST

ROLE_CHOICES = (('customer', _('customer')), ('acs', _('ACS chamber')), (
    ('acsadmin'), _('ACS admin')), ('acspartner', _('service station')))
OS_CHOICES = (('win', _('Windows')), ('gnu', _('GNU/Linux')))

if not os.path.exists(settings.EASY_RSA_DIR):
    raise OSError(
        "%s not found. Please check EASY_RSA_DIR value in settings.py" %
        settings.EASY_RSA_DIR)
if not os.path.isdir(settings.EASY_RSA_DIR):
    raise OSError(
        "%s is not a directory. Please check EASY_RSA_DIR value in settings.py"
        % settings.EASY_RSA_DIR)

PKITOOL = 'cd %s; . %s; ./pkitool %s' % (settings.EASY_RSA_DIR,
                                         settings.EASY_RSA_VARS_FILE, "%s")
REVOKEFULL = 'cd %s; . %s; ./revoke-full %s' % (
    settings.EASY_RSA_DIR, settings.EASY_RSA_VARS_FILE, "%s")

log = logging.getLogger(__name__)


class Client(models.Model):

    common_name = models.SlugField(
        _('cert name'),
        max_length=256,
        unique=True,
        blank=True,
        help_text=_(
            "Leave blank if you want to let the software assign a common name suitable for your subnet"))
    ip = models.GenericIPAddressField(
        _('IP address'),
        blank=True,
        null=True,
        help_text=_(
            "Leave blank if you want to let the software assign the first available for your network."))
    company = models.CharField(
        _('company'), max_length=256,
        blank=True, null=True)
    name = models.CharField(
        _('name'),
        max_length=128,
        help_text=_(
            "It should be Name Surname, or hostname. It has to be unique in company"))
    email = models.EmailField(blank=True, default="")
    operating_system = models.CharField(
        _('operating system'),
        max_length=32,
        choices=OS_CHOICES,
        blank=True,
        default=None,
        null=True)
    # Subnet can be null because of OpenVPNLog model needings (it logs whether client it sees in the network)
    subnet = models.ForeignKey('VPNSubnet',
                               verbose_name=_('Role'),
                               db_index=True,
                               null=True)
    enabled = models.BooleanField(_('enabled'), default=False)
    cert = models.TextField(_('certificate'), default="", blank=True)
    key = models.TextField(_('key'), default="", blank=True)

    # The can_access_to field, map one Client entry to many others.
    # It is used to bind:
    # 1. customers to ewons
    # 2. service stations to customers to let them access to every customer's ewon

    can_access_to = models.ManyToManyField("self", blank=True)

    cert_validity_start = models.DateTimeField(blank=True, null=True)
    cert_validity_end = models.DateTimeField(blank=True, null=True)
    cert_distribution_token = models.CharField(max_length=128,
                                               blank=True,
                                               null=True)
    cert_distribution_on = models.DateTimeField(blank=True, null=True)
    cert_download_on = models.DateTimeField(blank=True, null=True)
    cert_public_download_on = models.DateTimeField(blank=True, null=True)
    cert_revocation_on = models.DateTimeField(blank=True, null=True)

    created_on = models.DateTimeField(auto_now_add=True)

    @property
    def ca(self):
        return file(settings.CA_CERT).read()

    class Meta:
        unique_together = (('ip', 'enabled'), ('company', 'name', 'enabled'))
        ordering = ('subnet', 'company', 'name')

    def __unicode__(self):
        rv = self.common_name
        if self.company:
            rv += u" (%s)" % self.company
        return rv

    def get_cert_filename(self):

        basename = os.path.join(settings.EASY_RSA_KEYS_DIR, self.common_name)
        return basename + ".crt"

    def exist_cert(self):
        if os.path.exists(self.get_cert_filename()):
            return True
        return False

    def bind_cert(self):
        try:
            self.cert = file(self.get_cert_filename(), "r").read()
            self.key = file(self.get_cert_filename().replace(".crt", ".key"),
                            "r").read()
        except IOError as e:
            if e.errno == 2:
                raise CertNotFound(_("Certificate for %(obj)s"
                    " has not been found [file %(filename)s]."
                    " Please check your `easy-rsa` configuration in %(easy_rsa_dir)s") % {
                        'obj': self,
                        'easy_rsa_dir': settings.EASY_RSA_DIR,
                        'filename': e.filename,
                })
            else:
                raise

    def create_cert(self):
        """Create a certificate.

        1. Check if certificate has already been saved in db;
        2. If not -> try to bind a certificate with the same name already present in filesystem;
        3. If it is not present -> create a new certificate.

        """

        if not (self.cert or self.key):

            log.debug(
                "No certificate bound to client, check for an already existent certificate")
            try:
                self.bind_cert()
                log.debug("Found and already existent certificate for %s" %
                          self)
            except CertNotFound as e:

                log.debug("OK, no certificate found for %s. Creating it..." %
                          self)
                shell_cmd = PKITOOL % self.common_name
                try:
                    call_shell(shell_cmd)
                except CalledShellCommandError as e:
                    error_log = "%s | return code %s | %s" % (
                        e.shell_cmd, e.returncode, e.output)
                    client_log = ClientActionsLog(
                        action=ACTION_ERROR_CERT_CREATE,
                        note=error_log, client=self)
                    client_log.save()
                    raise CertCreationError(e.output)

                self.bind_cert()

            self.cert_distribution_token = None
            self.cert_distribution_on = None
            self.revocation_on = None
            client_log = ClientActionsLog(action=ACTION_CERT_CREATED, client=self)
            client_log.save()
            self.save()
        else:
            raise PermissionDenied(
                "You should delete certificate bound to this client before creating a new one")

        return True

    token_generator = tokens.CertDistributionTokenGenerator()

    def distribute_cert(self):
        """Create a token used to safe distribution for new certificate."""

        if not self.cert:
            self.create_cert()

        self.cert_distribution_on = datetime.datetime.now()
        self.save()
        self.cert_distribution_token = self.token_generator.make_token(self)
        client_log = ClientActionsLog(action=ACTION_CERT_DISTRIBUTED, client=self)
        client_log.save()
        self.save()

    def check_token(self, token, remote_ip):
        rv = self.token_generator.check_token(self, token)
        client_log = ClientActionsLog(
            action=ACTION_CERT_DISTRIBUTION_TOKEN_CHECKED,
            remote_ip=remote_ip, client=self,
            note="result %s" % rv)
        client_log.save()
        return rv

    def revoke_cert(self):
        p = subprocess.Popen(REVOKEFULL % self.common_name,
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()

        # Move files according to configuration
        crl_default_name = os.path.join(settings.EASY_RSA_KEYS_DIR, "keys",
                                        "crl.pem")

        # Update revocation timestamp
        self.revocation_on = datetime.datetime.now()
        self.enabled = False
        client_log = ClientActionsLog(action=ACTION_CERT_REVOKED, client=self,
                                      note="== OUTPUT == %s\n== ERROR == %s" %
                                      (stdout, stderr))
        client_log.save()
        self.save()

    def clean_ip(self):
        subnet = self.subnet

        # Check for non duplicates ip address

        for client in Client.objects.all():
            if (self.ip == client.ip) and (self.pk != client.pk):
                raise ValidationError(_(
                    "IP %(ip)s has already been taken by client %(client)s. Please change it"
                    % {
                        'ip': client.ip,
                        'client': client
                    }))

        if subnet.topology == "net30":
            last_octet = int(self.ip.split('.')[-1])
            if last_octet not in self.subnet.net30_valid_last_octet_list:
                msg = _(
                    "IP %(ip)s does not belong to valid IP addresses for subnet %(subnet)s") % {
                        'ip': self.ip,
                        'subnet': subnet
                    }
                log.error(msg)
                raise ValidationError(msg)

        else:
            bound_client_list = subnet.client_set.all().order_by('ip')

            if bound_client_list.filter(ip__exact=self.ip).count() > 1:

                msg = _(
                    "FOUND 2 IP %(ip)s IN THE SAME SUBNET %(subnet)s for clients %(clients)s") % {
                        'ip': self.ip,
                        'subnet': subnet,
                        'clients': ", ".join(map(lambda x: x.common_name,
                                                 bound_client_list.filter(
                                                     ip__exact=self.ip))),
                    }
                log.error(msg)
                raise ValidationError(msg)

    def fix_client_ip(self):

        log.info("Fixing client %s ip address %s" % (self, self.ip))

        # Move ip to the end of the list
        subnet = self.subnet
        bound_client_list = subnet.client_set.all().order_by('ip')
        ordered_ip4_aton_list = map(lambda obj: netutils.inet_aton(obj.ip),
                                    bound_client_list)
        ordered_ip4_aton_list.sort()

        aton_new_ip4 = subnet.get_next_aton_try(ordered_ip4_aton_list[-1])

        self.ip = netutils.inet_ntoa(aton_new_ip4)
        self.enabled = False
        self.save()
        log.info("Updated client %s with ip address %s" % (self, self.ip))

    def clean(self):

        if not self.ip:
            if self.subnet is None:
                raise ValidationError(_(
                    "Please specify a subnet before adding a new client"))
            self.ip = self.subnet.get_free_ip4()
        else:
            self.clean_ip()

        if not self.common_name:
            # If cn is blank it should be created
            if self.subnet.name.endswith('-ssl'):
                subnet_name = self.subnet.name[:-4].upper()
            else:
                subnet_name = self.subnet.name.upper()

            d = {
                'subnet': subnet_name,
                'company': slugify(self.company).upper(),
                'name': slugify(self.name).upper(),
            }

            self.common_name = self.subnet.common_name_template % d

        self.common_name = self.common_name.strip()

    def save(self, *args, **kw):
        self.clean()
        # If a cert is set to None, it means that it has been explicitly deleted
        if self.cert == u'':
            if self.pk:
                # If not set certificate and we are updating an object
                # Set certificate. This is needed because cert fields are disabled in admin UI
                old_client = Client.objects.get(pk=self.pk)
                self.cert = old_client.cert
                self.key = old_client.key
        elif self.cert is None:
            # It has been explicitly deleted
            self.cert = u''
            self.key = u''

        super(Client, self).save(*args, **kw)


class Subnet(models.Model):

    name = models.SlugField(_('name'), max_length=31, unique=True)
    human_name = models.CharField(_('human name'), max_length=128, unique=True)
    base = models.GenericIPAddressField(_('base'), unique=True)
    bits = models.PositiveSmallIntegerField(
        _('bits'))  # 0 - 32, ma forse 1 - 30
    default_gw = models.GenericIPAddressField(_('default gateway'))
    static_min = models.GenericIPAddressField(_('first available address'))
    static_max = models.GenericIPAddressField(_('last available address'))
    description = models.TextField(verbose_name=_('description'), blank=True)

    class Meta:
        verbose_name = _('subnet')
        verbose_name_plural = _('subnets')
        ordering = ['human_name']
        abstract = True

    class SubnetFullException(Exception):
        pass

    def __unicode__(self):
        return u"%s (%s/%d)" % (self.human_name, self.base, self.bits)

    def get_start_aton_try(self):
        return netutils.inet_aton(self.static_min)

    def get_next_aton_try(self, aton_try):
        return aton_try + 1

    def get_free_ip4(self):
        aton_min = netutils.inet_aton(self.static_min)
        aton_max = netutils.inet_aton(self.static_max)
        aton_try = self.get_start_aton_try()
        bound_client_list = self.client_set.all().order_by('ip')

        # print "AAAA %s %s - %s" % (self, self.static_min, self.static_max)
        # print bound_client_list
        if len(bound_client_list):

            ordered_ip4_aton_list = map(lambda obj: netutils.inet_aton(obj.ip),
                                        bound_client_list)
            ordered_ip4_aton_list.sort()

            for aton_ip4 in ordered_ip4_aton_list:

                if aton_ip4 >= aton_min:

                    if (aton_try == aton_max):
                        raise Subnet.SubnetFullException

                    elif (aton_try == aton_ip4):
                        # Try next one
                        aton_try = self.get_next_aton_try(aton_try)

                    else:
                        # Found!
                        rv = aton_try
                        break
        else:
            rv = aton_try

        return netutils.inet_ntoa(aton_try)

    def ip4_is_inside_subnet(self, addr):
        aton_laddr, aton_haddr = netutils.get_aton_bounds_from_cidr(self.base,
                                                                    self.bits)
        return netutils.ip_is_inside_inet_aton_range(addr, aton_laddr,
                                                     aton_haddr)

    def dotted_quad_netmask(self):
        num = 0
        for i in range(31, 31 - self.bits, -1):
            num += 2**i
        return netutils.inet_ntoa(num)

    dotted_quad_netmask.short_description = 'netmask'


class VPNSubnet(Subnet):
    """Adds VPN information to Subnet.
    """
    TOPOLOGY_NET30_VALID_LAST_OCTETS = [
        [1, 2], [5, 6], [9, 10], [13, 14], [17, 18], [21, 22], [25, 26],
        [29, 30], [33, 34], [37, 38], [41, 42], [45, 46], [49, 50], [53, 54],
        [57, 58], [61, 62], [65, 66], [69, 70], [73, 74], [77, 78], [81, 82],
        [85, 86], [89, 90], [93, 94], [97, 98], [101, 102], [105, 106],
        [109, 110], [113, 114], [117, 118], [121, 122], [125, 126], [129, 130],
        [133, 134], [137, 138], [141, 142], [145, 146], [149, 150], [153, 154],
        [157, 158], [161, 162], [165, 166], [169, 170], [173, 174], [177, 178],
        [181, 182], [185, 186], [189, 190], [193, 194], [197, 198], [201, 202],
        [205, 206], [209, 210], [213, 214], [217, 218], [221, 222], [225, 226],
        [229, 230], [233, 234], [237, 238], [241, 242], [245, 246], [249, 250],
        [253, 254]
    ]
    TOPOLOGY_CHOICES = (('subnet', 'subnet'),
                        ('net30', 'net30'), )
    # TODO: add can_access_to attribute

    bound_iface = models.CharField(verbose_name=_("bound interface"),
                                   max_length=16,
                                   blank=True)
    topology = models.CharField(verbose_name=_("topology"),
                                max_length=16,
                                choices=TOPOLOGY_CHOICES,
                                default=TOPOLOGY_CHOICES[0][0])
    common_name_template = models.CharField(
        verbose_name=_("common name template"),
        max_length=32,
        default="%(subnet)s-%(company)s-%(name)s",
        help_text=_(
            "Specify a python template string here. Allowed keys are 'name', 'company', 'subnet'"))
    config_server = models.TextField(_("server configuration"), blank=True)
    config_client = models.TextField(_("client configuration"), blank=True)

    @property
    def net30_valid_last_octet_list(self):
        return map(lambda x: x[0], self.TOPOLOGY_NET30_VALID_LAST_OCTETS)

    def __get_net30_next_aton_try_by_octets(self, octets):
        i = 0
        TOPO_VLO = self.TOPOLOGY_NET30_VALID_LAST_OCTETS
        try:
            while TOPO_VLO[i][0] <= int(octets[-1]):
                # DEBUG print "%s %s - %s" % ("a", self.topology, octets)
                i += 1
            octets[-1] = str(TOPO_VLO[i][0])
            a_try = ".".join(octets)
            aton_try = netutils.inet_aton(a_try)

        except IndexError:
            # Corner case. i.e. static_min is > x.y.z.253
            # Set it to the end. Convert to integer and increment by 2 to get (x.y.z.)+1.1
            octets[-1] = '255'
            a_try = ".".join(octets)
            aton_try = netutils.inet_aton(a_try) + 2

        return aton_try

    def get_start_aton_try(self):
        """Get first valid ntoa IP for VPN subnet.
        Manage specific OpenVPN topology and leave other cases to parent
        """
        if self.topology == 'net30':
            octets = self.static_min.split(".")
            rv = self.__get_net30_next_aton_try_by_octets(octets)
            # DEBUG print "START: %s try: %s" % (self, netutils.inet_ntoa(rv))
        else:
            # i.e. if self.topology == 'subnet':
            # But it could change in future implementations
            rv = super(VPNSubnet, self).get_start_aton_try()
        return rv

    def get_next_aton_try(self, aton_try):
        # DEBUG print "NEED NEXT: %s try: %s" % (self, netutils.inet_ntoa(aton_try))
        if self.topology == 'net30':
            a_try = netutils.inet_ntoa(aton_try)
            octets = a_try.split(".")
            rv = self.__get_net30_next_aton_try_by_octets(octets)
            # DEBUG print "FOUND: %s try: %s" % (self, netutils.inet_ntoa(rv))
        else:  # i.e. if self.topology == 'subnet':
            rv = super(VPNSubnet, self).get_next_aton_try(aton_try)

        return rv


class ClientActionsLog(models.Model):

    client = models.ForeignKey(Client)
    action = models.CharField(
        max_length=32)  # DEBUG: disabled, choices=ACTIONS_LIST)
    on = models.DateTimeField(auto_now=True)
    remote_ip = models.GenericIPAddressField(default="127.0.0.1")
    note = models.TextField(default="", blank=True)

    class Meta:
        ordering = ["-on"]
        get_latest_by = "on"
        verbose_name = "action log"

    def __unicode__(self):
        return u"%s %s on %s" % (self.client, self.action, self.on)
