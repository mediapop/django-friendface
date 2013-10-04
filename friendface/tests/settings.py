import os

SITE_ID = 1

APP_ROOT = os.path.abspath(os.path.dirname(__file__))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

AUTHENTICATION_BACKENDS = (
    'friendface.auth.backends.FacebookBackend',
    'django.contrib.auth.backends.ModelBackend'
)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django.contrib.sites',

    'friendface',

    'friendface.tests.account',
]

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'friendface.middleware.FacebookMiddleware',
)

SECRET_KEY = 'foobar'

TEST_RUNNER = 'discover_runner.DiscoverRunner'

ROOT_URLCONF = 'friendface.tests.urls'

STATIC_URL = '/static/'

AUTH_USER_MODEL = os.environ.get('AUTH_USER_MODEL', 'auth.User')
