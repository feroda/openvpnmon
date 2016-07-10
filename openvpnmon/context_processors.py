from django.conf import settings


def my_settings(request):
    return {
        "VERSION": settings.VERSION,
        "DEBUG": settings.DEBUG,
        "CERTS_PUBLIC_DOWNLOAD_URL_BASE":
        settings.CERTS_PUBLIC_DOWNLOAD_URL_BASE,
        "VPN_HOME_PAGE": settings.VPN_HOME_PAGE,
        "URL_PREFIX": settings.URL_PREFIX,
    }
