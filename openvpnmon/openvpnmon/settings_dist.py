
from default_settings import *

# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/
# DEBUG = False
# ALLOWED_HOSTS = ['openvpn.localdomain.it']
# SECRET_KEY = CHANGEME! 'x4fi-pw571hol%awdwnvldst&s&o+_uteczd6o$n4o5)u!a669'

# Specific openvpnmon settings
URL_PREFIX = ""

HARDENING = True

CERTS_PUBLIC_DOWNLOAD_URL_BASE = "https://localhost"
VPN_HOME_PAGE = "http://wwwvpnserver"
HOOK_CLIENT_MANAGE = os.path.join(BASE_DIR, "..", "extras", "client-manage.sh")
DEFAULT_DOMAIN = "demo.it"
