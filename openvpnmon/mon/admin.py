from django.contrib import admin
from mon.models import OpenVPNLog


class OpenVPNLogAdmin(admin.ModelAdmin):

    list_display = ('common_name', 'vpn_ip', 'when_connect', 'when_disconnect',
                    'vpn_iface', 'bytes_sent', 'bytes_received', 'public_ip')
    list_filter = ('vpn_iface', 'common_name')
    list_display_links = []

    date_hierarchy = 'when_connect'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True


admin.site.register(OpenVPNLog, OpenVPNLogAdmin)
