from django.conf import settings
import os, datetime, time, zipfile, zlib


def zipfile_info(zf):
    rv = ""
    for info in zf.infolist():
        rv += "%s" % info.filename
        rv += "%s %s" % ('\tComment:\t', info.comment)
        rv += "%s %s" % ('\tModified:\t', datetime.datetime(*info.date_time))
        rv += "%s %s %s" % ('\tSystem:\t\t', info.create_system,
                            '(0 = Windows, 3 = Unix)')
        rv += "%s %s" % ('\tZIP version:\t', info.create_version)
        rv += "%s %s %s" % ('\tCompressed:\t', info.compress_size, 'bytes')
        rv += "%s %s %s" % ('\tUncompressed:\t', info.file_size, 'bytes')
        rv += '\n'
    return rv


def zipfile_print_info(zf):
    print zipfile_info(zf)


def get_certs_zipfile(client, zipfilename):

    # Create ZIP file and serve
    compression = zipfile.ZIP_DEFLATED
    zf = zipfile.ZipFile(zipfilename, mode='w', compression=compression)
    zf.writestr("%s.crt" % settings.DOWNLOAD_CERT_CLIENT_BASENAME, client.cert)
    zf.writestr("%s.key" % settings.DOWNLOAD_KEY_CLIENT_BASENAME, client.key)
    zf.writestr("%s.crt" % settings.DOWNLOAD_CERT_CA_BASENAME, client.ca)
    if client.subnet.config_client:
        zf.writestr("%s.ovpn" % settings.DOWNLOAD_OPENVPNCONF_BASENAME_WIN,
                    client.subnet.config_client)
        zf.writestr("%s.conf" % settings.DOWNLOAD_OPENVPNCONF_BASENAME_GNU,
                    client.subnet.config_client)
    zf.close()
    return zf


def get_certs_zip_content_and_notes(client):

    zipfilename = '/tmp/zipc%s-%s.zip' % (client.pk, time.time())
    zf = get_certs_zipfile(client, zipfilename)

    f = file(zipfilename, mode="r")
    zipcontent = f.read()
    f.close()

    zipnotes = zipfile_info(zf)

    # Remove just created zipfile
    os.remove(zipfilename)
    return zipcontent, zipnotes
