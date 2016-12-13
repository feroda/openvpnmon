import datetime
import socket

from django.http import HttpResponseBadRequest, HttpResponse, Http404
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.views.decorators import staff_member_required

from django.shortcuts import get_object_or_404, redirect, render
from django.conf import settings

from base.models import Client, ACTION_CERT_DOWNLOADED, ClientActionsLog
from base.utils import zipfile_info, get_certs_zip_content_and_notes


def index(request):
    return redirect('%sadmin/' % settings.URL_PREFIX)


@staff_member_required
def display_certs(request):

    try:
        ct = int(request.GET["ct"])
        ids = request.GET["ids"]
    except KeyError:
        return HttpResponseBadRequest()

    id_list = map(int, ids.split(","))
    model = ContentType.objects.get(pk=ct).model_class()
    qs = model.objects.filter(pk__in=id_list)

    for client in qs:
        if not client.cert:
            client.create_cert()
    return render(request, "display_certs.html", {"objs": qs})


@staff_member_required
def display_distributions(request):

    try:
        ct = int(request.GET["ct"])
        ids = request.GET["ids"]
    except KeyError:
        return HttpResponseBadRequest()

    id_list = map(int, ids.split(","))
    model = ContentType.objects.get(pk=ct).model_class()
    qs = model.objects.filter(pk__in=id_list)

    for obj in qs:
        obj.distribute_cert()

    return render(request, "display_distributions.html",
                  {"objs": qs, "URL_PREFIX": settings.URL_PREFIX})


def pre_cert_download(request, client_id, token):
    """Display ZIP download link and instructions"""

    client = get_object_or_404(Client, pk=client_id)
    rv = client.check_token(token=token, remote_ip=request.META['REMOTE_ADDR'])

    if not rv:
        raise Http404

    return render(request, "display_download_page.html", {"client": client})


def _prepare_zip_certs_response(request, client):

    zipcontent, zipnotes = get_certs_zip_content_and_notes(client)
    content_type = 'application/zip'
    response = HttpResponse(zipcontent, content_type=content_type)
    response[
        'Content-Disposition'] = 'attachment; filename=%s.zip' % settings.DOWNLOAD_CERT_ARCHIVE_BASENAME
    client_log = ClientActionsLog(action=ACTION_CERT_DOWNLOADED,
                           remote_ip=request.META['REMOTE_ADDR'],
                           note=zipnotes, client=client)
    client_log.save()
    return response


def cert_download(request, client_id, token):
    """Download ZIP file and update public download date.
    After accessing this view the token will not be valid anymore"""

    client = get_object_or_404(Client, pk=client_id)
    remote_ip = request.META['REMOTE_ADDR']

    if not (client.check_token(token=token, remote_ip=remote_ip)):
        raise Http404

    response = _prepare_zip_certs_response(request, client)

    client.cert_download_on = datetime.datetime.now()
    # Update public download timestamp. This action invalidate the token.
    client.cert_public_download_on = client.cert_download_on
    client.save()

    return response


@staff_member_required
def private_cert_download(request, client_id):
    """Download ZIP file from admin interface (internal trusted network)
    and update download date.
    After accessing this view the download token is still valid"""

    client = get_object_or_404(Client, pk=client_id)
    remote_ip = request.META['REMOTE_ADDR']

    response = _prepare_zip_certs_response(request, client)

    # DO NOT update public download timestamp.
    client.cert_download_on = datetime.datetime.now()
    client.save()

    return response


def cert_download_complete(request):
    pass


def tcp_connect(request, client_id):
    """
    Verifies if a TCP connection can be established with the remote peer **host**:**port**.

    :returns: response with html snippet with list of checks
    :rtype: int

    """

    client = get_object_or_404(Client, pk=client_id)

    hostname = "%(name)s.%(domain)s" % {
        'name': client.common_name.lower(),
        'domain': settings.DEFAULT_DOMAIN,
    }
    port = 80

    dns_resolution = tcp_connection_up = None
    try:
        rv_addrinfo = socket.getaddrinfo(hostname, port, 2, 0, socket.SOL_TCP)
    except socket.gaierror, e:
        dns_up = {'check': False, 'descr': unicode(e.strerror)}
    except socket.timeout, t:
        dns_up = {'check': False, 'descr': unicode(t)}
    else:
        dns_up = {'check': True}

        # Try that dns resolved IP is what expected
        found_ip = rv_addrinfo[0][4][0]
        if found_ip != client.ip:
            dns_resolution = {'check': False,
                              'descr': u"%(found_ip)s != %(ip)s" % {
                                  'ip': client.ip,
                                  'found_ip': found_ip,
                              }}
        else:
            dns_resolution = {'check': True}

        # Try to connect  to found IP
        try:
            sock = socket.socket(*rv_addrinfo[:2])
            sock.settimeout(5)  # seconds
            sock.connect((found_ip, port))
            (peerhost, peerport) = sock.getpeername()
            tcp_connection_up = {'check': True}
        except Exception, e:
            tcp_connection_up = {'check': False, 'descr': unicode(e)}

    context = {
        'dns_up': dns_up,
        'dns_resolution': dns_resolution,
        'tcp_connection_up': tcp_connection_up,
        'hostname': hostname,
    }
    return render(request, "network_test.html", context)
