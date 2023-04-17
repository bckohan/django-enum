import os
from pathlib import Path

SECRET_KEY = 'psst'
SITE_ID = 1
USE_TZ = False

database = os.environ.get('DATABASE', 'postgres')

if database == 'sqlite':  # pragma: no cover
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'test.db',
            'USER': '',
            'PASSWORD': '',
            'HOST': '',
            'PORT': '',
        }
    }
elif database == 'postgres':  # pragma: no cover
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('POSTGRES_DB', 'postgres'),
            'USER': os.environ.get('POSTGRES_USER', 'postgres'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', ''),
            'HOST': os.environ.get('POSTGRES_HOST', ''),
            'PORT': os.environ.get('POSTGRES_PORT', ''),
        }
    }
elif database == 'mysql':  # pragma: no cover
    # import pymysql
    # pymysql.install_as_MySQLdb()
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            'NAME': os.environ.get('MYSQL_DB', 'test'),
            'USER': os.environ.get('MYSQL_USER', 'root'),
            'PASSWORD': os.environ.get('MYSQL_PASSWORD', ''),
            'HOST': os.environ.get('MYSQL_HOST', ''),
            'PORT': os.environ.get('MYSQL_PORT', ''),
        }
    }
# elif database == 'mariadb':  # pragma: no cover
#     pass
# elif database == 'oracle':  # pragma: no cover
#     pass

ROOT_URLCONF = 'django_enum.tests.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages'
            ],
        },
    },
]

MIDDLEWARE = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

INSTALLED_APPS = [
    'django_enum.tests.djenum',
    'django_enum.tests.tmpls',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
]

try:
    import rest_framework
    INSTALLED_APPS.insert(0, 'rest_framework')
except (ImportError, ModuleNotFoundError):  # pragma: no cover
    pass

try:
    import enum_properties
    INSTALLED_APPS.insert(0, 'django_enum.tests.enum_prop')
    INSTALLED_APPS.insert(0, 'django_enum.tests.edit_tests')
    INSTALLED_APPS.insert(0, 'django_enum.tests.examples')
except (ImportError, ModuleNotFoundError):  # pragma: no cover
    pass

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
)

STATIC_ROOT = Path(__file__).parent / 'global_static'
STATIC_URL = '/static/'

DEBUG = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

TEST_EDIT_DIR = Path(__file__).parent / 'edit_tests' / 'edits'
TEST_MIGRATION_DIR = Path(__file__).parent / 'edit_tests' / 'migrations'

REST_FRAMEWORK = {
    # no auth
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': [],
}