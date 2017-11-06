from django.conf.urls import url
from django.contrib import admin

from base import views as base_views
from django.conf import settings

urlpatterns = [
    url(r'^%s$' % settings.URL_PREFIX, base_views.index),
    url(r'^%sadmin/' % settings.URL_PREFIX, admin.site.urls),
    url(r'^%sdisplay_certs/' % settings.URL_PREFIX,
        base_views.display_certs,
        name="display-certs"),
    url(r'^%sdisplay_distributions/' % settings.URL_PREFIX,
        base_views.display_distributions,
        name="display-distributions"),
    url(r'^%scert_download/(?P<client_id>\d+)-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$'
        % settings.URL_PREFIX,
        base_views.pre_cert_download,
        name="pre-cert-download"),
    url(r'^%scert_download/(?P<client_id>\d+)-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/download/$'
        % settings.URL_PREFIX,
        base_views.cert_download,
        name="cert-download"),
    url(r'^%scert_download/done/$' % settings.URL_PREFIX,
        base_views.cert_download_complete,
        name="cert-download-complete"),
    # This is safe because is not bound to external network
    url(r'^%sprivate_cert_download/(?P<client_id>\d+)/download/$' %
        settings.URL_PREFIX,
        base_views.private_cert_download,
        name="private-cert-download"),
    url(r'^%stcp_connect/(?P<client_id>\d+)/$' % settings.URL_PREFIX,
        base_views.tcp_connect,
        name="tcp-connect"),
]
