from pathlib import Path
from django import VERSION as django_version

SECRET_KEY = 'psst'
SITE_ID = 1

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

if django_version[0:2] >= (5, 0):
    INSTALLED_APPS.insert(0, 'django_enum.tests.db_default')

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