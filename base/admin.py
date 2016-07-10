from django.contrib import admin
from django.core import urlresolvers
from django.utils.translation import ugettext_lazy as _
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect
from django.contrib import messages

from base.models import Client, VPNSubnet, ClientActionsLog


def disable_field(field):
    disable_opts = {
        'readonly': 'readonly',
        'disabled': 'true',
    }
    field.widget.attrs.update(disable_opts)
    field.help_text = ""


class ClientForm(forms.ModelForm):

    def __new__(cls, *args, **kw):
        cls = super(ClientForm, cls).__new__(cls, *args, **kw)
        disable_field(cls.base_fields['cert'])
        disable_field(cls.base_fields['key'])
        cls.base_fields['cert'].widget.attrs.update({'rows': 40})
        cls.base_fields['key'].widget.attrs.update({'rows': 20})
        return cls

    class Meta:
        model = Client
        exclude = []

    def clean_name(self):
        cnames = Client.objects.filter(name=self.cleaned_data["name"])
        if cnames.count() > 1 or (cnames.count() == 1 and
                                  self.instance.pk != cnames[0].pk):
            raise forms.ValidationError(_("Name must be unique"))

        return self.cleaned_data["name"]


class ClientAdmin(admin.ModelAdmin):

    form = ClientForm
    save_on_top = True
    list_display = ('subnet_with_link', 'company', 'name', 'common_name', 'ip',
                    'has_certificate', 'cert_download_on', 'enabled')
    list_display_links = ('name', )
    list_filter = ('subnet', 'company')
    list_editable = ('ip', )
    fieldsets = ((None,
                  {
                      'fields': ('company',
                                 'name',
                                 'email',
                                 'subnet',  #'can_access_to'
                                 )
                  }),
                 ("Extra", {
                     'fields': ('operating_system', 'ip', 'common_name'),
                     'classes': ('collapse', )
                 }),
                 (_("Certificate"), {
                     'fields': (('cert', 'key'), ),
                     'classes': ('collapse', )
                 }), )
    filter_horizontal = ('can_access_to', )
    actions = ['create_cert', 'show_cert', 'revoke_cert', 'publish_cert',
               'download_cert']
    search_fields = ('name', 'common_name', 'ip', 'company')

    def subnet_with_link(self, obj):
        url = urlresolvers.reverse('admin:base_vpnsubnet_change',
                                   args=(obj.subnet.id, ))
        return u'<a href="%s">%s</a>' % (url, obj.subnet)

    subnet_with_link.allow_tags = True
    subnet_with_link.short_description = _("subnet")
    subnet_with_link.admin_order_field = 'subnet'

    def has_certificate(self, obj):
        return bool(obj.cert)

    has_certificate.boolean = True

    def create_cert(self, request, queryset):
        """Create certificates for all selected clients.

        Do not raise exception, but show user an info message.
        """

        has_cert = False
        for obj in queryset.all():
            if obj.cert:
                messages.error(request, _(
                    "You cannot create a certificate for %s because it has already one")
                               % obj)
                url = urlresolvers.reverse('admin:base_client_changelist')
                has_cert = True

        if not has_cert:

            for obj in queryset.all():
                try:
                    obj.create_cert()
                except Exception as e:
                    messages.error(request, _(
                        "Certificate creation for %(obj)s failed, error: %(e)s")
                                   % {
                                       'obj': obj,
                                       'e': e
                                   })

    create_cert.short_description = _("Create a new certificate")

    def revoke_cert(self, request, queryset):
        for obj in queryset.all():
            obj.revoke_cert()

    revoke_cert.short_description = _("Revoke certificate")

    def renew_cert(self, request, queryset):
        pass

    renew_cert.short_description = _("Renew certificate")

    def show_cert(self, request, queryset):
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        ct = ContentType.objects.get_for_model(queryset.model)
        url = u"%s?ct=%s&ids=%s" % (urlresolvers.reverse("display-certs"),
                                    ct.pk, ",".join(selected))
        return HttpResponseRedirect(url)

    show_cert.short_description = _("View certificates")

    def publish_cert(self, request, queryset):

        verify_certs = True
        for el in queryset:
            if not el.cert:
                messages.error(request, _(
                    "No certificate has been created for client %s, cannot publish")
                               % el)
                url = urlresolvers.reverse('admin:base_client_changelist')
                verify_certs = False

        if verify_certs:

            selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
            ct = ContentType.objects.get_for_model(queryset.model)
            url = u"%s?ct=%s&ids=%s" % (
                urlresolvers.reverse("display-distributions"), ct.pk,
                ",".join(selected))

        return HttpResponseRedirect(url)

    publish_cert.short_description = _("Publish certificates")

    def download_cert(self, request, queryset):
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        if len(selected) > 1:
            messages.error(
                request,
                _("You can download only certificates for one client a time"))
            url = urlresolvers.reverse('admin:base_client_changelist')
        elif not queryset[0].cert:
            messages.error(
                request, _("No certificate has been created for this client"))
            url = urlresolvers.reverse('admin:base_client_changelist')
        else:
            url = urlresolvers.reverse('private-cert-download',
                                       kwargs={"client_id": int(selected[0])})
        return HttpResponseRedirect(url)

    download_cert.short_description = _("Download certificates")


class VPNSubnetAdmin(admin.ModelAdmin):

    save_on_top = True
    list_display = ('__unicode__', 'description')
    fieldsets = (
        (None, {
            'fields': (('name', 'human_name'),
                       ('base', 'bits'),
                       'default_gw',
                       ('static_min', 'static_max'), )
        }),
        ('VPN settings', {
            'fields':
            ('topology', 'bound_iface', 'config_server', 'config_client')
        }),
        ("Extra", {
            'fields': ('description', 'common_name_template'),
            'classes': ('collapse', )
        }), )
    radio_fields = {"topology": admin.VERTICAL, }


class ClientActionsLogAdmin(admin.ModelAdmin):

    list_display = ('on', 'client', 'action')
    list_filter = ('on', 'client__subnet', 'action')
    list_display_links = []
    date_hierarchy = 'on'

    search_fields = ['action', 'client__common_name']


admin.site.register(Client, ClientAdmin)
admin.site.register(VPNSubnet, VPNSubnetAdmin)
admin.site.register(ClientActionsLog, ClientActionsLogAdmin)
