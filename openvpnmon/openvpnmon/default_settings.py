# Django settings for openvpnmon project.
import os


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION = file(os.path.join(BASE_DIR, 'VERSION')).read().strip()
PROJECT_ROOT = BASE_DIR  # DEPRECATED

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'x4fi-pw571hol%awdwnvldst&s&o+_uteczd6o$n4o5)u!a669'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'openvpnmon.urls'

INSTALLED_APPS = [
    'django.contrib.admin', 'django.contrib.auth',
    'django.contrib.contenttypes', 'django.contrib.sessions',
    'django.contrib.messages', 'django.contrib.staticfiles', 'base', 'mon'
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR + "/templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                # 'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.contrib.messages.context_processors.messages',
                'openvpnmon.context_processors.my_settings',
            ],
            'debug': True,
        },
    },
]

WSGI_APPLICATION = 'openvpnmon.wsgi.application'

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME':
        'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/static/'

# Logging facility
LOG_PATH = os.environ.get('LOG_PATH', BASE_DIR)
LOG_FILE = os.path.join(LOG_PATH, 'openvpnmon.log')
LOG_FILE_DEBUG = os.path.join(LOG_PATH, 'openvpnmon_debug.log')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format':
            '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'logfile': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE,
            'maxBytes': 1048576,
            'backupCount': 5,
            'formatter': 'simple'
        },
        'logfile_debug': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE_DEBUG,
            'maxBytes': 1048576,
            'backupCount': 10,
            'formatter': 'verbose'
        },
        #        'mail_admins': {
        #            'level': 'ERROR',
        #            'class': 'django.utils.log.AdminEmailHandler',
        #        }
    },
    'loggers': {
        'django': {
            'handlers': ['null'],
            'propagate': True,
            'level': 'INFO',
        },
        'django.request': {
            'handlers': ['logfile'],
            'level': 'ERROR',
            'propagate': False,
        },
        'openvpnmon': {
            'handlers': ['console', 'logfile', 'logfile_debug'],
            'level': 'DEBUG',
        }
    }
}

# Specific django-openvpn settings
URL_PREFIX = ""

HARDENING = True

EASY_RSA_DIR = os.path.join(BASE_DIR, "..", "extras", "easy-rsa")
EASY_RSA_KEYS_DIR = os.path.join(EASY_RSA_DIR, "keys")
EASY_RSA_VARS_FILE = os.path.join(EASY_RSA_DIR, "vars")
CA_CERT = os.path.join(EASY_RSA_KEYS_DIR, 'ca.crt')
CERTS_PUBLIC_DOWNLOAD_URL_BASE = "https://localhost"
VPN_HOME_PAGE = "http://wwwvpnserver"
HOOK_CLIENT_MANAGE = os.path.join(BASE_DIR, "..", "extras", "client-manage.sh")

# Name for downloaded cert archive file and files within it
DOWNLOAD_CERT_ARCHIVE_BASENAME = "certs"
DOWNLOAD_CERT_CLIENT_BASENAME = "vpnclient"
DOWNLOAD_KEY_CLIENT_BASENAME = "vpnclient"
DOWNLOAD_CERT_CA_BASENAME = "ca"
DOWNLOAD_OPENVPNCONF_BASENAME_GNU = DOWNLOAD_OPENVPNCONF_BASENAME_WIN = "subnet"
OPENVPN_CONF_NAME = 'vpn.conf'

# GIVEN TOKEN IS VALID FOR
# DJANGO USES PASSWORD_RESET_TIMEOUT_DAYS.. I use it to my needs
TOKEN_TIMEOUT_DAYS = 1
PASSWORD_RESET_TIMEOUT_DAYS = TOKEN_TIMEOUT_DAYS

DATETIME_FORMAT = "D d M Y, H:i"
DEFAULT_DOMAIN = "demo.it"

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
